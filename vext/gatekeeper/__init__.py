"""
GateKeeper finder / loader implementations imported from here.

Things change quite a lot in python3.5 where imp is deprecated.
"""
import glob
import imp
import logging
import os
import re
import site
import sys

from genericpath import isdir, isfile
from os.path import join, abspath, splitext, relpath, normpath

from vext.env import getsyssitepackages, in_venv
from vext.helpers import get_extra_path
from vext import registry, logger

log_blocks = 'VEXT_LOG_BLOCKS' in os.environ
remember_blocks = 'VEXT_REMEMBER_BLOCKS' in os.environ
blocked_imports = registry.blocked_imports
allowed_modules = registry.allowed_modules
added_dirs = registry.added_dirs

if 'VEXT_ALLOWED_MODULES' in os.environ:
    allowed_modules.update(re.search(r',| ', os.environ['VEXT_ALLOWED_MODULES']).groups())

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
                    exec (line, globals(), locals())
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


class VextError(Exception):
    def __init__(*args, **kwargs):
        Exception.__init__(*args, **kwargs)


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

        # Get the name relative to SITEDIR ..
        filepath = self.module_info[1]
        fullname = splitext( \
            relpath(filepath, getsyssitepackages()) \
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
        other_paths = [p for p in sys.path if p not in [sitedir, GatekeeperFinder.PATH_TRIGGER]] + ['.']
        try:
            module_info = imp.find_module(fullname, other_paths)
            if module_info:
                logger.debug("found module %s in sitedir", fullname)
                return
        except ImportError:
            try:
                # Now check if in site packages and needs gatekeeping
                module_info = imp.find_module(fullname, [sitedir, self.path_entry])
                if module_info:
                    logger.debug("found module %s in sitedir or subdirectory", fullname)
                    return GateKeeperLoader(module_info)
                else:
                    raise ImportError()
            except ImportError:
                logger.debug("%s not found in: %s", fullname, os.pathsep.join(other_paths))
                # Not in site packages, pass
                return


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

    keys = ['modules', 'pths', 'test_import', 'install_hints', 'extra_paths']
    data = yaml.load(f)
    parsed = dict()
    ## pattern = re.compile("^\s+|\s*,\s*|\s+$")
    for k in keys:
        v = data.get(k, [])
        # Items are always lists
        if isinstance(v, basestring):
            parsed[k] = [m for m in re.split(r",| ", v)]
            # parsed[k] = re.split(pattern, v)
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
    vext_dir = join(sys.prefix, "share/vext/specs")
    return sorted(glob.glob(join(vext_dir, normpath('*.vext'))))


def load_specs():
    bad_specs = set()
    last_error = None

    for fn in spec_files():
        logger.debug("load spec: %s", fn)
        if fn in bad_specs:
            # Don't try and load the same bad spec twice
            continue

        try:
            spec = open_spec(open(fn))

            for module in spec['modules']:
                logger.debug("allow module: %s", module)
                allowed_modules.add(module)

            for path_name in spec.get('extra_paths', []):
                extra_path = get_extra_path(path_name)
                if isdir(extra_path):
                    os.environ['PATH'] += env_t(os.pathsep + extra_path)
                    sys.path.append(extra_path)
                    added_dirs.add(extra_path)
                else:
                    logger.warn("Could not add extra path: {0}".format(extra_path))

            sys_sitedir = getsyssitepackages()
            for pth in [pth for pth in spec['pths'] or [] if pth]:
                try:
                    logger.debug("open pth: %s", pth)
                    pth_file = join(sys_sitedir, pth)
                    addpackage(sys_sitedir, pth_file, added_dirs)
                    init_path()  # TODO
                except IOError as e:
                    # Path files are optional..
                    logging.debug('No pth found at %s', pth_file)
                    pass

        except Exception as e:
            bad_specs.add(fn)
            err_msg = 'error loading spec %s: %s' % (fn, e)
            if last_error != err_msg:
                logging.error(err_msg)
            last_error = err_msg

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
        logging.debug('No virtualenv active py:[%s]', sys.executable)
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
