"""
This file is run by the system python, and outputs paths the
import mechanism in the virtualenv will need to be able to
import libraries from.
"""

import json
import os
import sys

from distutils.sysconfig import get_python_lib

"""
Return paths from the system python
"""
def py_info():
    data = { 
        "path": os.environ['PATH'].split(os.pathsep),
        "sys.path": sys.path,
        "sitepackages": get_python_lib()
    }
    return data

if __name__ == '__main__':
    print json.dumps(py_info())