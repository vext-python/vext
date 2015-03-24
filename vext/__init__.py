import traceback

import collections
import glob
import imp
import logging
import os
import site
import subprocess
import sys
import vext.registry

from distutils.sysconfig import get_python_lib

#if 'VIRTUAL_ENV' in os.environ:
#    VIRTUAL_ENV=os.path.abspath(['VIRTUAL_ENV'])
#elif:
#    # Run directly from the venv
#    for p in os.environ['PATH'].split(os.pathsep):
#        if p and 
#            os.path.isfile(os.path.join(p, python)):
#            if sys.executable != p:
#                VIRTUAL_ENV=os.path.normpath(p, '..')
#            else:
#                VIRTUAL_ENV=None
#            break

log_blocks='VEXT_LOG_BLOCKS' in os.environ
remember_blocks='VEXT_REMEMBER_BLOCKS' in os.environ
blocked_imports = vext.registry.blocked_imports
allowed_modules=vext.registry.allowed_modules
if 'VEXT_ALLOWED_MODULES' in os.environ:
    allowed_modules.add(*[m.strip() for m in os.environ['VEXT_ALLOWED_MODULES'].split(' ,')])

vext_pth=os.path.join(get_python_lib(), 'vext_importer.pth')
added_dirs = vext.registry.added_dirs
_syssitepackages = None
_in_venv = None

try:
    unicode
except NameError:
    # Python 3
    basestring = unicode = str

if os.name == 'nt':
    # Windows needs environment variables + paths to be strings
    env_t = str
else:
    env_t = unicode

class VextException(Exception):
    def __init__(*args, **kwargs):
        Exception.__init__(*args, **kwargs)

def findsyspy():
    """
    :return: First python in that is not sys.executable 
             or sys.executable if not found
    """
    python=os.path.basename(sys.executable)
    for folder in os.environ['PATH'].split(os.pathsep):
        if folder and \
            not folder.startswith(sys.exec_prefix) and\
            os.path.isfile(os.path.join(folder, python)):
            return os.path.join(folder, python)
    else:
        return sys.executable

def in_venv():
    global _in_venv
    if _in_venv is not None:
        return _in_venv

    if 'VIRTUAL_ENV' in os.environ:
        _in_venv = True
    else:
        # Find first python in path ... if its not this one,
        # ...we are in a different python
        python=os.path.basename(sys.executable)
        for p in os.environ['PATH'].split(os.pathsep):
            if os.path.isfile(os.path.join(p, python)):
                _in_venv=sys.executable != p
                break
    
    return _in_venv

    

def getsyssitepackages():
    """
    Get site-packages from system python
    """
    global _syssitepackages
    if not _syssitepackages:
        env = os.environ
        python = findsyspy()
        code = 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'
        cmd = [python, '-c', code]

        _syssitepackages = subprocess.check_output(cmd, env=env).decode('utf-8').splitlines()[0]
    return _syssitepackages


class GateKeeperLoader(object):
    """
    Only allow known modules to import from the system site packages
    """
    def __init__(self, module_info):
        self.module_info = module_info

    def load_module(self, name):
        """
        Only lets modules in allowed_modules be loaded, others
        will get an ImportError
        """
        global log_blocks, remember_blocks, blocked_imports

        # Get the name relative to SITEDIR .. 
        filepath = self.module_info[1]
        fullname = os.path.splitext(\
            os.path.relpath(filepath, getsyssitepackages())\
            )[0].replace(os.sep, '.')

        basename = fullname.split('.')[0]
        if basename not in allowed_modules:
            if remember_blocks:
                blocked_imports.add(fullname)
            if log_blocks:
                raise ImportError("Vext blocked import of '%s'" % basename)
            else:
                # Standard error message
                raise ImportError("No module named %s" % basename)

        if not name in sys.modules:
            module = imp.load_module(fullname, *self.module_info)
            sys.modules[fullname] = module

        return sys.modules[fullname]


class GatekeeperFinder(object):
    """
    Only allow known modules to import from the system site packages
    """
    PATH_TRIGGER = 'VextFinder.PATH_TRIGGER'

    def __init__(self, path_entry):
        global added_dirs
        self.path_entry = path_entry

        sitedir = getsyssitepackages()
        if not path_entry in (sitedir, GatekeeperFinder.PATH_TRIGGER):
            return None
        else:
            raise ImportError()

    def find_module(self, fullname, path=None):
        if fullname in sys.modules: 
            return sys.modules[fullname]

        sitedir = getsyssitepackages()
        # Check paths other than system sitepackages first
        other_paths = [ p for p in sys.path if p in [sitedir, GatekeeperFinder.PATH_TRIGGER]] + ['.']
        try:
            module_info = imp.find_module(fullname, other_paths)
            if module_info:
                return None
        except ImportError:
            try:
                # Now check if in site packages and needs gatekeeping
                module_info = imp.find_module(fullname, [sitedir, self.path_entry])
                if module_info:
                    return GateKeeperLoader(module_info)
                else:
                    raise ImportError()
            except ImportError:
                # Not in site packages, pass
                return None


def addpackage(sitedir, pthfile, known_dirs=None):
    """
    Wrapper for site.addpackage

    Try and work out which directories are added by
    the .pth and add them to the known_dirs set    
    """
    known_dirs = set(known_dirs or [])
    with open(os.path.join(sitedir, pthfile)) as f:
        for n, line in enumerate(f):
            if line.startswith("#"):
                continue
            line = line.rstrip()
            if line:
                if line.startswith(("import ", "import\t")):
                    exec(line)
                    continue
                else:
                    p_rel = os.path.join(sitedir, line)
                    p_abs = os.path.abspath(line)
                    if os.path.isdir(p_rel):                        
                        os.environ['PATH'] += env_t(os.pathsep + p_rel)
                        sys.path.append(p_rel)
                        added_dirs.add(p_rel)
                    elif os.path.isdir(p_abs):
                        os.environ['PATH'] += env_t(os.pathsep + p_abs)
                        sys.path.append(p_abs)
                        added_dirs.add(p_abs)

    if os.path.isfile(pthfile):
        site.addpackage(sitedir, pthfile, known_dirs)
    else:
        logging.debug("pth file '%s' not found")


def init_path():
    """
    Add any new modules that are directories to the PATH
    """
    sitedir = getsyssitepackages()
    env_path = os.environ['PATH'].split(os.pathsep)
    for module in allowed_modules:
        p = os.path.join(sitedir, module)
        if os.path.isdir(p) and not p in env_path:
            os.environ['PATH'] += env_t(os.pathsep + p)


def open_spec(f):
    """
    :param f: file object with spec data

    spec file is a yaml document that specifies which modules
    can be loaded.

    modules - list of base modules that can be loaded
    pths    - list of .pth files to load
    """
    import yaml
    keys = ['modules', 'pths']
    data = yaml.load(f)
    parsed = dict()
    for k in keys:
        v = data.get(k, [])
        # Items are always lists
        if isinstance(v, basestring):
            parsed[k] = v.split()
        else:
            parsed[k] = v

    return parsed

def spec_files():
    """
    :return: Iterator over spec files.
    """
    sitedir=get_python_lib()
    return glob.glob(os.path.join(sitedir, os.path.normpath('vext/specs/*.vext')))

def load_specs():
    global added_dirs
    
    bad_specs = set()
    last_error=None

    for fn in spec_files():
        if fn in bad_specs:
            # Don't try and load the same bad spec twice
            continue

        try:
            spec = open_spec(open(fn))

            for module in spec['modules']:
                allowed_modules.add(module)

            sys_sitedir = getsyssitepackages()
            for pth in [ pth for pth in spec['pths'] or [] if pth]:
                try:
                    pth_file=os.path.join(sys_sitedir, pth)
                    addpackage(sys_sitedir, pth_file, added_dirs)
                    init_path() # TODO
                except IOError as e:
                    # Path files are optional..
                    logging.debug('No pth found at %s', pth_file)
                    pass

        except Exception as e:
            bad_specs.add(fn)
            err_msg='error loading spec %s: %s' % (fn, e)
            if last_error != err_msg:
                logging.error(err_msg)
            last_error=err_msg

    if bad_specs:
        raise VextError('Error loading spec files: %s' % ', '.join(bad_specs))

def install_importer():
    """
    If in a virtualenv then load spec files to decide which
    modules can be imported from system site-packages and
    install path hook.
    """
    logging.debug('install_importer')
    if not in_venv():
        logging.warning('No virtualenv active')
        return False

    if GatekeeperFinder.PATH_TRIGGER not in sys.path:
        load_specs()
        sys.path.append(GatekeeperFinder.PATH_TRIGGER)
        sys.path_hooks.append(GatekeeperFinder)
        return True
