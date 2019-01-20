"""
GateKeeper finder / loader implementations imported from here.

Things change quite a lot in python3.5 where imp is deprecated.


Useful environment variables (Used for debug, may change)

VEXT_DISABLED=1                         Disable vext by not adding it to sys.path
VEXT_LOG_BLOCKS=1                       Store any blocked imports in registry.blocked_imports
VEXT_ALLOWED_MODULES=module1,module2    Extra modules to allow
VEXT_DEBUG_LOG=1                        Debug logging

"""
import glob
import imp
import logging
import os
import re
import site
import sys
from contextlib import contextmanager
from distutils.sysconfig import get_python_lib
from os.path import isdir, isfile, join, basename, abspath, splitext, relpath
from vext import registry, logger
from vext.conf import open_spec
from vext.env import findsyspy, getsyssitepackages, in_venv
from vext.helpers import get_extra_path

try:
    unicode
except NameError:
    # Python 3
    basestring = unicode = str

log_blocks = 'VEXT_LOG_BLOCKS' in os.environ
remember_blocks = 'VEXT_REMEMBER_BLOCKS' in os.environ
blocked_imports = registry.blocked_imports  # if remember_blocks is True blocked imports are added here
allowed_modules = registry.allowed_modules  # populated by .vext files
added_dirs = registry.added_dirs
disable_vext = bool(os.environ.get('VEXT_DISABLED', False))
if hasattr(sys, 'argv') and 'setup.py' in sys.argv[0:2]:  # Somehow sys doesn't always have argv here
    print("Running during setup - temporarily disable vext")
    disable_vext = True  # Hack: - need a better way to disable during setup of vext itself

if 'VEXT_ALLOWED_MODULES' in os.environ:
    allowed_modules.update(re.findall(r'[^,\s]+', os.environ['VEXT_ALLOWED_MODULES']))

if os.name == 'nt':
    # Windows needs environment variables + paths to be strings
    env_t = str
else:
    env_t = unicode


def fix_path(p):
    """
    Convert path pointing subdirectory of virtualenv site-packages
    to system site-packages.

    Destination directory must exist for this to work.

    >>> fix_path('C:\\some-venv\\Lib\\site-packages\\gnome')
    'C:\\Python27\\lib\\site-packages\\gnome'
    """
    venv_lib = get_python_lib()

    if p.startswith(venv_lib):
        subdir = p[len(venv_lib) + 1:]

        for sitedir in getsyssitepackages():
            fixed_path = join(sitedir, subdir)
            if isdir(fixed_path):
                return fixed_path

    return p


@contextmanager
def fixup_paths():
    """
    Fixup paths added in .pth file that point to the virtualenv
    instead of the system site packages.

    In depth:  .PTH can execute arbitrary code, which might
    manipulate the PATH or sys.path

    :return:
    """
    original_paths = os.environ.get('PATH', "").split(os.path.pathsep)
    original_dirs = set(added_dirs)
    yield

    # Fix PATH environment variable
    current_paths = os.environ.get('PATH', "").split(os.path.pathsep)
    if original_paths != current_paths:
        changed_paths = set(current_paths).difference(set(original_paths))
        # rebuild PATH env var
        fixed_paths = []
        for path in current_paths:
            if path in changed_paths:
                fixed_paths.append(env_t(fix_path(path)))
            else:
                fixed_paths.append(env_t(path))
        os.environ['PATH'] = os.pathsep.join(fixed_paths)

    # Fix added_dirs
    if added_dirs != original_dirs:
        for path in set(added_dirs.difference(original_dirs)):
            fixed_path = fix_path(path)
            if fixed_path != path:
                print("Fix %s >> %s" % (path, fixed_path))
                added_dirs.remove(path)
                added_dirs.add(fixed_path)

                i = sys.path.index(path)  # not efficient... but shouldn't happen often
                sys.path[i] = fixed_path

                if env_t(fixed_path) not in os.environ['PATH']:
                    os.environ['PATH'].append(os.pathsep + env_t(fixed_path))


def addpackage(sys_sitedir, pthfile, known_dirs):
    """
    Wrapper for site.addpackage

    Try and work out which directories are added by
    the .pth and add them to the known_dirs set

    :param sys_sitedir: system site-packages directory
    :param pthfile: path file to add
    :param known_dirs: set of known directories
    """
    with open(join(sys_sitedir, pthfile)) as f:
        for n, line in enumerate(f):
            if line.startswith("#"):
                continue
            line = line.rstrip()
            if line:
                if line.startswith(("import ", "import\t")):
                    exec (line, globals(), locals())
                    continue
                else:
                    p_rel = join(sys_sitedir, line)
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
        site.addpackage(sys_sitedir, pthfile, known_dirs)
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

    def __init__(self, module_info, sitedir):
        self.module_info = module_info
        self.sitedir = sitedir

    def load_module(self, name):
        """
        Only lets modules in allowed_modules be loaded, others
        will get an ImportError
        """

        # Get the name relative to SITEDIR ..
        filepath = self.module_info[1]
        fullname = splitext( \
            relpath(filepath, self.sitedir) \
            )[0].replace(os.sep, '.')

        modulename = filename_to_module(fullname)
        if modulename not in allowed_modules:
            if remember_blocks:
                blocked_imports.add(fullname)
            if log_blocks:
                raise ImportError("Vext blocked import of '%s'" % modulename)
            else:
                # Standard error message
                raise ImportError("No module named %s" % modulename)

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
        # TODO Need lots of unit tests around this
        module = sys.modules.get(fullname)
        if module and hasattr(module, "load_module"):
            # After reload module can be missing load_module
            return module

        sitedirs = getsyssitepackages()
        # Check paths other than system sitepackages first
        other_paths = [p for p in sys.path if p not in sitedirs + [GatekeeperFinder.PATH_TRIGGER, '.']]
        try:
            for other_path in other_paths:
                try:
                    module_info = imp.find_module(fullname, [other_path])
                    if module_info:
                        logger.debug("found module %s in other path [%s]", fullname, other_path)
                        return
                except ImportError:
                    continue
            else:
                raise ImportError()
        except ImportError:
            try:
                # Now check if in site packages and needs gatekeeping
                for sitedir in sitedirs:
                    try:
                        module_info = imp.find_module(fullname, [sitedir, self.path_entry])
                        if module_info:
                            logger.debug("found module %s in sitedir or subdirectory [%s]", fullname, sitedir)
                            return GateKeeperLoader(module_info, sitedir)
                    except ImportError:
                        logger.debug("%s not found in: %s", fullname, os.pathsep.join(other_paths))
                        continue
            except ImportError:
                ### TODO
                # Need to debug why this catch is needed, removing it stops things working...
                # something is subtly weird here.
                return


def init_path():
    """
    Add any new modules that are directories to the PATH
    """
    sitedirs = getsyssitepackages()
    for sitedir in sitedirs:
        env_path = os.environ['PATH'].split(os.pathsep)
        for module in allowed_modules:
            p = join(sitedir, module)
            if isdir(p) and not p in env_path:
                os.environ['PATH'] += env_t(os.pathsep + p)


def test_imports(modules, py=None):
    """
    Iterate through test_imports and try and import them

    :return: iterator of  ((success, module_name), ...)
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


def spec_dir():
    """
    :return: Directory vext files are installed to
    """
    return join(sys.prefix, "share/vext/specs")


def spec_files():
    """
    :return: Iterator over spec files.
    """
    return sorted(glob.glob(join(spec_dir(), '*.vext')))


def spec_files_flat():
    """
    :return: basenames of intalled spec files
    """
    return [basename(vext_file) for vext_file in spec_files()]


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
                    logger.warn("Skipped adding nonexistant path: {0}".format(extra_path))

            sys_sitedirs = getsyssitepackages()
            for sys_sitedir in sys_sitedirs:
                with fixup_paths():
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

    if disable_vext:
        logging.debug('Vext disabled by environment variable')
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
