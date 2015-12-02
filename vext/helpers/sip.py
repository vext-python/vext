"""
SIP is the build system for Qt

This helper, enables us to find qt5, at least on Linux
"""
import vext
import vext.env


def extra_paths():
    """
    :return: extra paths
    """
    # TODO - this is only tested on Ubuntu for now
    #        there must be a better way of getting
    #        the sip directory.
    dirs = {}
    try:
        @vext.env.run_in_syspy
        def run(*args):
            import sipconfig
            config = sipconfig.Configuration()
            dirs = {
                "sip.default_sip_dir": config.default_sip_dir,
            }
            return dirs
        dirs = run()
        return dirs
    except ImportError:
        return dirs
