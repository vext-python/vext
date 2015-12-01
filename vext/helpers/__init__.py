__all__ = ["sip"]

from . import sip

path_helpers = {
    "sip": sip
}

path_cache = {}  # {helper: {paths} }

def get_extra_path(name):
    """
    :param name: name in format helper.path_name

    sip.default_sip_dir
    """
    # Paths are cached in path_cache
    helper_name, _, key = name.partition(".")
    helper = path_helpers.get(helper_name)
    if not helper:
        raise ValueError("Helper '{0}' not found.".format(helper))
    if name not in path_cache:
        extra_paths = helper.extra_paths()
        path_cache.update(extra_paths)
    extra_path = path_cache.get(name)
    if not extra_path:
        raise ValueError("Helper '{0}' has no path called {1}".format(helper_name, name))
    return extra_path

