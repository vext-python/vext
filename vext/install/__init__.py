import logging

from distutils import sysconfig
from os.path import join

from vext.env import run_in_syspy
from vext.gatekeeper import open_spec
from vext import logger


def add_vext(vext_file):
    """
    Create an entry for 'setup.py': 'data_files' that will
    install a vext
    """
    dest_dir = join(sysconfig.get_python_lib(), 'vext/specs')
    return (dest_dir, [vext_file])


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
            if logger.level == logging.DEBUG:
                for k, v in result.keys:
                    logger.debug("%s: %s", k, v)
            elif not all(result.values()):
                print(install_hint)
    if success:
        print("OK")
    return success
