import json
import os
import sys
import subprocess

def memoize(f):
    memo = {}
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = f(*args)
            memo[args] = rv
            return rv
    return wrapper

@memoize
def syspy_home():
    return os.environ.get('_OLD_VIRTUAL_PYTHONHOME')

@memoize
def syspy_info():
    """
    :return: dict of system python $PATH and sys.path
    """
    env = os.environ # TODO 
    python = os.path.join(syspy_home(), 'python')
    pyinfo = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'syspy',
        'pyinfo.py'
        )

    cmd = [python, [pyinfo]]

    output = subprocess.check_output(cmd, env=env).decode('utf-8').splitlines()[0]
    return json.loads(output)

def main():
    if 'VIRTUAL_ENV' in os.environ:
        #print syspy_home()
        print syspy_info()
    else:
        print 'Not running in virtualenv.'

if __name__ == '__main__':
    main()
