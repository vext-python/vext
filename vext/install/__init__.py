import logging

from setuptools.command import install_lib
from distutils import sysconfig


def add_vext(vext_file):
    """
    Create an entry for 'setup.py': 'data_files' that will
    install a vext
    """
    dest_dir = os.path.join(sysconfig.get_python_lib(), 'vext/specs')
    return (dest_dir, [vext_file])


def check_installable(vext):
    """
    Check that imports in 'test_imports' succeed
    otherwise display message in 'install_hint'
    """
    install_hint = vext.get('install_hint', 'Failed')
    for m in vext.get('test_import', '').split():
        try:
            __import__(m)
        except:
            logging.warning(install_hint)
            return False    
    return True


class VextInstallLib(install_lib.install_lib):
    """
    Install / Uninstall .pth file which enables the import hook.
    """
    def install(self):
        """
        Add / remove the vext_importer.pth in site_packages
        """
        if 'install' in argv:
            src=path.join(here, 'vext_importer.pth')
            dest=path.join(site_packages_path, 'vext_importer.pth')
            try:
                copyfile(src, dest)
            except:
                pass
            return install_lib.install_lib.install(self) 
        if 'uninstall' in argv:  # TODO - uninstall doesn't work like this
            dest=path.join(site_packages_path, 'vext_importer.pth')
            try:
                unlink(dest)
            except:            
                pass
            return []
        return install_lib.install_lib.install(self)

