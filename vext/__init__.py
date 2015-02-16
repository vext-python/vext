import collections
import glob
import imp
import logging
import os
import site
import subprocess
import sys
import yaml
import vext.registry

from distutils.sysconfig import get_python_lib

VIRTUAL_ENV=os.path.abspath(os.environ.get('VIRTUAL_ENV'))

allowed_modules=vext.registry.allowed_modules
added_dirs = vext.registry.added_dirs
_syssitepackages = None

def findsyspy():
    """
    :return: First python in PATH outside of virtualenv
    """
    python = os.path.basename(sys.executable)
    for p in os.environ['PATH'].split(os.pathsep):
        if p and \
            not p.startswith(VIRTUAL_ENV) and\
            os.path.isfile(os.path.join(p, python)):
            return p

def getsyssitepackages(syspy_home=None):
    """
    Get site-packages from system python
    """
    global _syssitepackages
    if not _syssitepackages:
        syspy_home = syspy_home or findsyspy()
        env = os.environ
        python = os.path.join(syspy_home, os.path.basename(sys.executable))
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
        # Get the name relative to SITEDIR .. 
        filepath = self.module_info[1]
        fullname = os.path.splitext(\
            os.path.relpath(filepath, getsyssitepackages())\
            )[0].replace(os.sep, '.')

        basename = fullname.split('.')[0]
        if basename not in allowed_modules:
            raise ImportError("Install library that provides module '%s' to virtualenv or add module to Vext.allowed_modules" % basename)

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
        if path_entry == sitedir:
            return None

        if path_entry.startswith(sitedir):
            for p in added_dirs:
                if path_entry.startswith(p):
                    raise ImportError()
            for m in allowed_modules:
                if path_entry == os.path.join(sitedir, m):
                    raise ImportError()

            return None

        if path_entry == GatekeeperFinder.PATH_TRIGGER:
            # Activate this finder for special paths
            return None
        else:
            raise ImportError()

    def find_module(self, fullname, path=None):
        if fullname in sys.modules:            
            return sys.modules[fullname]

        try:
            sitedir = getsyssitepackages()
            module_info = imp.find_module(fullname, [sitedir, self.path_entry])
            if module_info:
                return GateKeeperLoader(module_info)

            return None
        except Exception as e:
            raise

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
                    exec line
                    continue
                else:
                    p_rel = os.path.join(sitedir, line)
                    p_abs = os.path.abspath(line)
                    if os.path.isdir(p_rel):
                        os.environ['PATH'] += os.pathsep + p_rel
                        sys.path.append(p_rel)
                        added_dirs.add(p_rel)
                    elif os.path.isdir(p_abs):
                        os.environ['PATH'] += os.pathsep + p_abs
                        sys.path.append(p_abs)
                        added_dirs.add(p_abs)

    site.addpackage(sitedir, pthfile, known_dirs)


def init_path():
    sitedir = getsyssitepackages()
    env_path = os.environ['PATH'].split(os.pathsep)
    for module in allowed_modules:
        p = os.path.join(sitedir, module)
        if os.path.isdir(p) and not p in env_path:
            os.environ['PATH'] += os.pathsep + p


def open_spec(f):
    """
    :param f: file object with spec data

    spec file is a yaml document that specifies which modules
    can be loaded.

    modules - list of base modules that can be loaded
    pths    - list of .pth files to load
    """
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

def load_specs():
    global added_dirs
    sitedir=get_python_lib()
    for fn in glob.glob(os.path.join(sitedir, os.path.normpath('vext/specs/*.vext'))):
        try:
            spec = open_spec(open(fn))

            for module in spec['modules']:
                allowed_modules.add(module)

            sitedir = getsyssitepackages()
            for pth in [ pth for pth in spec['pths'] or [] if pth]:
                addpackage(sitedir, os.path.join(sitedir, pth), added_dirs)
                init_path() # TODO

        except Exception as e:
            logging.warning('error loading spec %s: %s' % (fn, e))
            raise

def install_importer():
    """
    If in a virtualenv then load spec files to decide which
    modules can be imported from system site-packages and
    install path hook.
    """
    logging.warning('install_importer')
    if not os.environ.get('VIRTUAL_ENV'):
        logging.warning('No virtualenv')
        return False

    if GatekeeperFinder.PATH_TRIGGER not in sys.path:
        load_specs()
        sys.path.append(GatekeeperFinder.PATH_TRIGGER)
        sys.path_hooks.append(GatekeeperFinder)
        return True
