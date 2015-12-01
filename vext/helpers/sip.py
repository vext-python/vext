"""
SIP is the build system for Qt

This helper, enables us to find qt5, at least on Linux
"""
import vext

def extra_paths():
    import ast
    """
    :return: extra paths
    """
    # TODO - this is only tested on Ubuntu for now
    #        there must be a better way of getting
    #        the sip directory.
    dirs = {}
    try:
        @vext.run_in_syspy
        def run():
            import sipconfig
            config = sipconfig.Configuration()
            dirs = {
                "sip.default_sip_dir": config.default_sip_dir,
            }
            print(dirs)
        output = run()
        dirs = ast.literal_eval(output)
        return dirs
    except ImportError:
        return dirs
