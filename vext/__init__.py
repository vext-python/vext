import glob
import imp
import json
import logging
import os
import yaml
import sys
import subprocess

here = os.path.abspath(os.path.dirname(__file__))
spec_dir = os.path.join(here, 'specs')
spec_files = list(glob.glob(os.path.join(spec_dir, '*.vext')))

"""
Custom module loader to allow external modules to be loaded from a virtualenv.

Only modules specified in spec files '.vext' are allowed.
"""

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

    >>> syspy_info()
    { u'path': ['C:\\Program Files\\... '], u'sys.path': ['C:\\temp...'] }
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


def find_dlls(dlls, search_path=None):
    '''
    Search OS path for dlls
    :param dlls: List of dlls to search for (without extensions)
    :yield: dll, path
    '''
    paths = set()
    if search_path is None:
        search_path = os.environ.get('PATH', "").split(os.pathsep)
    for d in search_path:
        for name in dlls:
            fullpath = os.path.join(d, name + '.dll')
            if os.path.exists(fullpath):
                paths.add(d)
    return list(paths)


def _parse_spec(spec):    
    _spec = dict(**spec)
    dlls = spec.get('dlls', [])
    if isinstance(dlls, basestring):
        dlls = [dlls]

    if dlls:
        search_path = syspy_info()['path']
        _spec.setdefault('paths', [])
        #_spec['paths'].extend( find_dlls(dlls, search_path) )        
        
    return _spec


def load_spec(path):
    """
    Load and parse .vext spec for external library
    """
    with open(path) as f:
        data = yaml.load(f)
        return _parse_spec(data)

def load_vext_specs():
    """
    Load spec files
    """
    global spec_path

    specs = {}
    for spec_file in spec_files:
        spec = load_spec(spec_file)

        _module = spec['module']
        specs[_module] = spec

    return specs




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
    specs = load_vext_specs()

    def __init__(self, *args):
        pass

    @classmethod
    def hook_inst(cls):
        if not cls.hook:
            cls.hook = VextImporter()
        return cls.hook

    def find_module(self, fullname, path=None):
        """
        If there is a .vext spec file then can be handled by
        this module.
        """
        base_module, _, _ = fullname.partition('.')
        spec = self.specs.get(base_module)
        if spec:
            return self
        else:
            # No spec file, nothing we can handle
            return None
 
    def load_module(self, fullname):
        """

        """
        if fullname in sys.modules:
            return sys.modules[fullname]

        base_module, _, _ = fullname.partition('.')
        spec = self.specs.get(base_module)

        if not spec:
            # Somehow no spec for this module
            logging.warning('No .vext spec for module %s' % fullname)
            return

        # Save sys.path and $PATH
        _sys_path = sys.path
        _path = str(os.environ.get('PATH'))

        # Add the PATH from the system python
        env_path = '' + os.environ['PATH']
        env_path += os.pathsep + os.pathsep.join(syspy_info()['path'])
        env_path += os.pathsep.join(spec.get('paths', []))

        sys.path.extend( syspy_info()['sys.path'] )
        os.environ['PATH'] = env_path

        # given a name like cairo._cairo
        # find the file and directory it is in
        module, _, name = fullname.rpartition('.')
        subdir = module.replace('.', os.sep)

        # Find the module in sitepackages
        # TODO - Search other dirs in pythonpath ?
        p = os.path.join(syspy_info()['sitepackages'], subdir)
        module_info = imp.find_module(name, [p])
        try:
            module = imp.load_module(fullname, *module_info) # name
        except:
            raise

        # restore PATH and sys.path
        os.environ['PATH'] = _path
        sys.path = _sys_path


        sys.modules[fullname] = module
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
try:
    install_importer()
except:
    logging.warning("ERROR")
