import glob
import imp
import logging
import os
import re
import site
import subprocess
import sys
import vext.registry

from distutils.sysconfig import get_python_lib
from os.path import abspath, basename, join, isdir, isfile, normpath, splitext, relpath

logger = logging.getLogger("vext")
if "VEXT_DEBUG_LOG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)

#if 'VIRTUAL_ENV' in os.environ:
#    VIRTUAL_ENV=abspath(['VIRTUAL_ENV'])
#elif:
#    # Run directly from the venv
#    for p in os.environ['PATH'].split(os.pathsep):
#        if p and 
#            isfile(join(p, python)):
#            if sys.executable != p:
#                VIRTUAL_ENV=normpath(p, '..')
#            else:
#                VIRTUAL_ENV=None
#            break

log_blocks='VEXT_LOG_BLOCKS' in os.environ
remember_blocks='VEXT_REMEMBER_BLOCKS' in os.environ
blocked_imports = vext.registry.blocked_imports
allowed_modules=vext.registry.allowed_modules

orig_prefix = normpath(join( get_python_lib(), '..', 'orig-prefix.txt'))

if 'VEXT_ALLOWED_MODULES' in os.environ:
    allowed_modules.update(re.search(r',| ', os.environ['VEXT_ALLOWED_MODULES']).groups())

vext_pth=join(get_python_lib(), 'vext_importer.pth')
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
    :return: system python executable
    """
    if not in_venv():
        return sys.executable

    python=basename(sys.executable)
    with open( orig_prefix ) as op:
        prefix = op.read()

        for folder in os.environ['PATH'].split(os.pathsep):
            if folder and \
                folder.startswith(prefix) and\
                isfile(join(folder, python)):
                return join(folder, python)




def in_venv():
    """
    :return: True if in running from a virtualenv

    Has to detect the case where the python binary is run
    directly, so VIRTUAL_ENV may not be set
    """
    global _in_venv
    if _in_venv is not None:
        return _in_venv

    if not os.path.isfile(orig_prefix):
        logger.debug("in_venv no orig_prefix [%s]", orig_prefix)
        # TODO - check this is actually valid !
        _in_venv = False
        return _in_venv

    if 'VIRTUAL_ENV' in os.environ:
        logger.debug("in_venv VIRTUAL_ENV set.")
        _in_venv = True
    else:
        # Find first python in path ... if its not this one,
        # ...we are in a different python
        python=basename(sys.executable)
        for p in os.environ['PATH'].split(os.pathsep):
            py_path = join(p, python)
            if isfile(py_path):
                logger.debug("in_venv py_at [%s] return: %s", (py_path, sys.executable != py_path))
                _in_venv=sys.executable != py_path
                break
    
    return _in_venv

    
def getsyssitepackages():
    """
    Get site-packages from system python
    """
    global _syssitepackages
    if not _syssitepackages:
        if not in_venv():
            _syssitepackages = get_python_lib()
            return _syssitepackages
        env = os.environ
        python = findsyspy()
        code = 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'
        cmd = [python, '-c', code]

        _syssitepackages = subprocess.check_output(cmd, env=env).decode('utf-8').splitlines()[0]
    return _syssitepackages

def filename_to_module(filename):
    """
    convert a filename like html5lib-0.999.egg-info to html5lib
    """
    find = re.compile(r"^[^.|-]*")
    name = re.search(find, filename).group(0)
    return name

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
        fullname = splitext(\
            relpath(filepath, getsyssitepackages())\
            )[0].replace(os.sep, '.')

        basename = filename_to_module(fullname)
        if basename not in allowed_modules:
            if remember_blocks:
                blocked_imports.add(fullname)
            if log_blocks:
                raise ImportError("Vext blocked import of '%s'" % basename)
            else:
                # Standard error message
                raise ImportError("No module named %s" % basename)

        if name not in sys.modules:
            try:
                logger.debug("load_module %s %s", name, self.module_info)
                module = imp.load_module(name, *self.module_info)
            except Exception as e:
                logger.debug(e)
                raise
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
        if path_entry in (sitedir, GatekeeperFinder.PATH_TRIGGER):
            logger.debug("handle entry %s", path_entry)
            return
        else:
            logger.debug("not handling entry %s", path_entry)
            raise ImportError()

    def find_module(self, fullname, path=None):
        if fullname in sys.modules: 
            return sys.modules[fullname]

        sitedir = getsyssitepackages()
        # Check paths other than system sitepackages first
        other_paths = [ p for p in sys.path if p not in [sitedir, GatekeeperFinder.PATH_TRIGGER]] + ['.']
        try:
            module_info = imp.find_module(fullname, other_paths)
            if module_info:
                logger.debug("found module in sitedir")
                return
        except ImportError:
            try:
                # Now check if in site packages and needs gatekeeping
                module_info = imp.find_module(fullname, [sitedir, self.path_entry])
                if module_info:
                    logger.debug("found module in sitedir or subdirectory")
                    return GateKeeperLoader(module_info)
                else:
                    raise ImportError()
            except ImportError:
                logger.debug("not found in %s", other_paths)
                # Not in site packages, pass
                return


def addpackage(sitedir, pthfile, known_dirs=None):
    """
    Wrapper for site.addpackage

    Try and work out which directories are added by
    the .pth and add them to the known_dirs set    
    """
    known_dirs = set(known_dirs or [])
    with open(join(sitedir, pthfile)) as f:
        for n, line in enumerate(f):
            if line.startswith("#"):
                continue
            line = line.rstrip()
            if line:
                if line.startswith(("import ", "import\t")):
                    exec(line, globals(), locals())
                    continue
                else:
                    p_rel = join(sitedir, line)
                    p_abs = abspath(line)
                    if isdir(p_rel):                        
                        os.environ['PATH'] += env_t(os.pathsep + p_rel)
                        sys.path.append(p_rel)
                        added_dirs.add(p_rel)
                    elif isdir(p_abs):
                        os.environ['PATH'] += env_t(os.pathsep + p_abs)
                        sys.path.append(p_abs)
                        added_dirs.add(p_abs)

    if isfile(pthfile):
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
        p = join(sitedir, module)
        if isdir(p) and not p in env_path:
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
    keys = ['modules', 'pths', 'test_import', 'install_hints']
    data = yaml.load(f)
    parsed = dict()
    ## pattern = re.compile("^\s+|\s*,\s*|\s+$")
    for k in keys:
        v = data.get(k, [])
        # Items are always lists
        if isinstance(v, basestring):
            parsed[k] = [ m for m in re.split(r",| ", v) ]
            #parsed[k] = re.split(pattern, v)
        else:
            parsed[k] = v

    return parsed

def test_imports(modules, py=None):
    """
    Iterate through test_imports and try and import them    
    """
    # TODO - allow passing different python to run remotely
    for module in modules:
        if not module:
            continue  # TODO - removeme once spec loading is fixed        
        try:
            __import__(module)
            yield True, module
        except:
            yield False, module

        

def spec_files():
    """
    :return: Iterator over spec files.
    """
    vext_dir=join(sys.prefix, "share/vext/specs")
    return sorted(glob.glob(join(vext_dir, normpath('*.vext'))))


def load_specs():
    global added_dirs
    
    bad_specs = set()
    last_error=None

    for fn in spec_files():
        print(fn)
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
                    pth_file=join(sys_sitedir, pth)
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
        logging.debug('No virtualenv active py:[%]' % sys.executable)
        return False

    if GatekeeperFinder.PATH_TRIGGER not in sys.path:
        try:
            load_specs()
            sys.path.append(GatekeeperFinder.PATH_TRIGGER)
            sys.path_hooks.append(GatekeeperFinder)
        except Exception as e:
            """
            Dont kill other programmes because of a vext error
            """
            logger.info(str(e))
            if logger.getEffectiveLevel() == logging.DEBUG:
                raise
        
        logging.debug("importer installed")
        return True
