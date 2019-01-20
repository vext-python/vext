import logging

from os.path import basename, isdir, join, normpath
from os import makedirs

from shutil import copyfile
from sys import prefix

from vext.env import run_in_syspy
from vext.conf import open_spec
from vext import logger, vext_pth


DEFAULT_PTH_CONTENT = """\
# Attempt to install the vext importer without blowing up everything 
# if vext was uninstalled in the meantime.
#
# Lines beginning with 'import' are executed, so import sys to get
# going.
import sys; exec("try:\\n import vext\\n vext.install_importer()\\nexcept:\\n pass")
"""


def check_sysdeps(vext_files):
    """
    Check that imports in 'test_imports' succeed
    otherwise display message in 'install_hints'
    """

    @run_in_syspy
    def run(*modules):
        result = {}
        for m in modules:
            if m:
                try:
                    __import__(m)
                    result[m] = True
                except ImportError:
                    result[m] = False
        return result

    success = True
    for vext_file in vext_files:
        with open(vext_file) as f:
            vext = open_spec(f)
            install_hint = " ".join(vext.get('install_hints', ['System dependencies not found']))

            modules = vext.get('test_import', '')
            logger.debug("%s test imports of: %s", vext_file, modules)
            result = run(*modules)
            if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                for k, v in result.items():
                    logger.debug("%s: %s", k, v)
            if not all(result.values()):
                success = False
                print(install_hint)
    return success


def install_vexts(vext_files, verify=True):
    """
    copy vext_file to sys.prefix + '/share/vext/specs'

    (PIP7 seems to remove data_files so we recreate something similar here)
    """
    if verify and not check_sysdeps(vext_files):
        return

    spec_dir = join(prefix, 'share/vext/specs')
    try:
        makedirs(spec_dir)
    except OSError as e:
        if not isdir(spec_dir):
            logger.error("Error making spec directory [%s]: %r" % (spec_dir, e))

    for vext_file in vext_files:
        dest = normpath(join(spec_dir, basename(vext_file)))
        try:
            logger.debug("%s > %s" % (vext_file, dest))
            copyfile(vext_file, dest)
            yield vext_file, dest
        except IOError as e:
            logger.error("Could not copy %s %r" % (vext_file, e))


def create_pth():
    """
    Create the default PTH file
    :return:
    """
    if prefix == '/usr':
        print("Not creating PTH in real prefix: %s" % prefix)
        return False
    with open(vext_pth, 'w') as f:
        f.write(DEFAULT_PTH_CONTENT)
    return True
