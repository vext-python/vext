"""
Utility functions for handling the python environment (virtual or otherwise)
"""
import ast
import inspect
import os
import subprocess
import sys
from distutils.sysconfig import get_python_lib
from genericpath import isfile
from os.path import basename, join, normcase, normpath, realpath
from textwrap import dedent
from vext import logger


def run_in_syspy(f):
    """
    Decorator to run a function in the system python

    :param f:
    :return:
    """
    fname = f.__name__
    code_lines = inspect.getsource(f).splitlines()

    code = dedent("\n".join(code_lines[1:]))  # strip this decorator

    # add call to the function and print it's result
    code += dedent("""\n
        import sys
        args = sys.argv[1:]
        result = {fname}(*args)
        print("%r" % result)
    """).format(fname=fname)

    env = os.environ
    python = findsyspy()
    logger.debug("Create function for system python\n%s" % code)

    def call_f(*args):
        cmd = [python, '-c', code] + list(args)
        output = subprocess.check_output(cmd, env=env).decode('utf-8')
        result = ast.literal_eval(output)
        return result

    return call_f


def in_venv():
    """
    :return: True if in running from a virtualenv

    Has to detect the case where the python binary is run
    directly, so VIRTUAL_ENV may not be set
    """
    global _in_venv
    if _in_venv is not None:
        return _in_venv

    if not (os.path.isfile(ORIG_PREFIX_TXT) or os.path.isfile(PY_VENV_CFG)):
        logger.debug("in_venv no orig_prefix_txt [%s]", ORIG_PREFIX_TXT)
        logger.debug("in_venv no py_venv_cfg [%s]", PY_VENV_CFG)
        # TODO - check this is actually valid !
        _in_venv = False
        return _in_venv

    if 'VIRTUAL_ENV' in os.environ:
        logger.debug("in_venv VIRTUAL_ENV set.")
        _in_venv = True
    else:
        # Find first python in path ... if its not this one,
        # ...we are in a different python
        python = basename(sys.executable)
        for p in os.environ['PATH'].split(os.pathsep):
            py_path = join(p, python)
            if isfile(py_path):
                logger.debug("in_venv py_at [%s] return: %s", (py_path, sys.executable != py_path))
                _in_venv = sys.executable != py_path
                break

    return _in_venv


def getsyssitepackages():
    """
    :return: list of site-packages from system python
    """
    global _syssitepackages
    if not _syssitepackages:
        if not in_venv():
            _syssitepackages = get_python_lib()
            return _syssitepackages

        @run_in_syspy
        def run(*args):
            import site
            return site.getsitepackages()

        output = run()
        _syssitepackages = output
        logger.debug("system site packages: %s", _syssitepackages)
    return _syssitepackages


def findsyspy():
    """
    :return: system python executable
    """
    if not in_venv():
        return sys.executable

    python = basename(realpath(sys.executable))
    prefix = None
    if HAS_ORIG_PREFIX_TXT:
        with open(ORIG_PREFIX_TXT) as op:
            prefix = op.read()
    elif HAS_PY_VENV_CFG:
        prefix = getattr(sys, "_home")

    if not prefix:
        return None

    for folder in os.environ['PATH'].split(os.pathsep):
        if folder and \
                normpath(normcase(folder)).startswith(normcase(normpath(prefix))) and \
                isfile(join(folder, python)):
            return join(folder, python)

    # OSX: Homebrew doesn't leave python in the PATH
    if isfile(join(prefix, "bin", python)):
        return join(prefix, "bin", python)


ORIG_PREFIX_TXT = normpath(join(get_python_lib(), '..', 'orig-prefix.txt'))
PY_VENV_CFG = normpath(join(get_python_lib(), '..', '..', '..', 'pyvenv.cfg'))

HAS_ORIG_PREFIX_TXT = os.path.isfile(ORIG_PREFIX_TXT)
HAS_PY_VENV_CFG = os.path.isfile(PY_VENV_CFG)

_syssitepackages = None
_in_venv = None
