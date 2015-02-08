"""
This file is run by the system python, and outputs paths the
import mechanism in the virtualenv will need to be able to
import libraries from.
"""

import json
import os
import sys

"""
Return paths from the system python
"""
def py_info():
    data = { 
        "path": os.environ['PATH'],
        "sys.path": sys.path
    }
    return data

if __name__ == '__main__':
    print json.dumps(py_info())