import logging

from os.path import basename, join, normpath
from os import makedirs

from shutil import copyfile
from sys import prefix

from vext.env import run_in_syspy
from vext.gatekeeper import open_spec
from vext import logger


def check_sysdeps(*vext_files):
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


def install_vexts(vext_files):
    """
    copy vext_file to sys.prefix + '/share/vext/specs'

    (PIP7 seems to remove data_files so we recreate something similar here)
    """
    if not check_sysdeps(vext_files):
        return

    spec_dir = join(prefix, 'share/vext/specs')
    try:
        makedirs(spec_dir)
    except OSError:
        pass

    for vext_file in vext_files:
        dest = normpath(join(spec_dir, basename(vext_file)))
        try:
            copyfile(vext_file, dest)
        except IOError:
            pass
