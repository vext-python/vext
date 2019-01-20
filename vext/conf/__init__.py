import re

try:
    unicode
except NameError:
    # Python 3
    basestring = unicode = str

def open_spec(f):
    """
    :param f: file object with spec data

    spec file is a yaml document that specifies which modules
    can be loaded.

    modules - list of base modules that can be loaded
    pths    - list of .pth files to load
    """
    import ruamel.yaml as yaml

    keys = ['modules', 'pths', 'test_import', 'install_hints', 'extra_paths']
    data = yaml.safe_load(f)
    parsed = dict()
    ## pattern = re.compile("^\s+|\s*,\s*|\s+$")
    for k in keys:
        v = data.get(k, [])
        # Items are always lists
        if isinstance(v, basestring):
            parsed[k] = [m for m in re.split(r",| ", v)]
            # parsed[k] = re.split(pattern, v)
        else:
            parsed[k] = v

    return parsed
