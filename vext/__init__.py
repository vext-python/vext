import json
import logging
import os
import sys
import subprocess

# Utility functions
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

# vext importer.
#
# If a module is specified in a .vext file then attempt to import it from the
# system python instead of the virtualenv.
#
class VextImporter(object):
    """
    Allow loading of external modules, if yaml spec file for them exists.
    """

    hook = None
    modules = {}

    def __init__(self, *args):
        pass

    @classmethod
    def hook_inst(cls):
        if not cls.hook:
            cls.hook = VextImporter()
        return cls.hook

    def find_spec(self, fullname):
        pass
 
    def find_module(self, fullname, path=None):
        #specs = spec_files()

        logging.warning('find_module %s' % fullname)
        #if fullname in AllowExternal.modules:
        #   return AllowExternal.modules[fullname]
        #else:

        name = fullname.split('.')[0]
        spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + '.yml')
        if os.path.exists(spec_path):
            # - parse the spec and get the module
            logging.warning('%s > %s' % (fullname, name))
            AllowExternal.modules[fullname] = spec_path

            return self
            # TODO
        else:
            logging.warning('%s doesnt exist' % fullname)
            return None
 
    def load_module(self, name):
        logging.warning('load_module %s' % name)
        if name in sys.modules:
            logging.warning("return sys_module %s" % name)

        # TODO here:    
        spec_path = AllowExternal.modules.get(name)
        if not spec_path:
            logging.warning('no spec %s' % fullname)
            return
        else:
            logging.warning('got spec %s ' % spec_path)

        sys.path.extend(['C:\\tools\\python2\\Lib\\site-packages', 'C:\\tools\\python2\\Lib\\site-packages\\cairo'])
        # pth = sys.path
        # if name != 'cairo._cairo':
        #     logging.warning("load sys module")
        #     #pth = ''
        #     #sys.path.extend(['C:\\tools\\python2\\Lib\\site-packages', 'C:\\tools\\python2\\Lib\\site-packages\\cairo', 'C:\\tools\\python2\\Lib\\site-packages\\cairo\\_cairo.pyd'])
        #     module_info = imp.find_module(name, sys.path)
        #     module = imp.load_module(name, *module_info)
        # else:
        #     logging.warning("do something special")
        #     fullpath = 'C:\\tools\\python2\\Lib\\site-packages\\cairo\\_cairo.pyd'
        #     f = open(fullpath, 'r')
        #     module = imp.load_module(
        #         'cairo._cairo',
        #         f, 
        #         fullpath,
        #         ('.pyd', 'rb', 3))
        sys.modules[name] = module

        logging.warning("Herp derp " + name)
        return module


def install_importer():
    """
    Install import hook.
    """
    logging.warning("Install import hook.")
    sys.meta_path = [VextImporter.hook_inst()]

def main():
    if 'VIRTUAL_ENV' in os.environ:
        #print syspy_home()
        logging.warning(syspy_info())
    else:
        logging.warning('Not running in virtualenv.')

#if __name__ == '__main__':
#    main()

logging.warning('name:' + __name__)
install_importer()
