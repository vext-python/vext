"""
Utility functions for handling the python environment (virtual or otherwise)
"""
from distutils.sysconfig import get_python_lib
from genericpath import isfile

import ast
import inspect
import os
from os.path import basename, join, normcase, normpath, realpath
import subprocess
import sys
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
    with open(orig_prefix) as op:
        prefix = op.read()

        for folder in os.environ['PATH'].split(os.pathsep):
            if folder and \
                normpath(normcase(folder)).startswith(normcase(normpath(prefix))) and\
                    isfile(join(folder, python)):
                        return join(folder, python)

        # Homebrew doesn't leave python in the PATH
        if isfile(join(prefix, "bin", python)):
            return join(prefix, "bin", python)



orig_prefix = normpath(join( get_python_lib(), '..', 'orig-prefix.txt'))
_syssitepackages = None
_in_venv = None
