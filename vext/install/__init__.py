import logging

from setuptools.command import install_lib
from distutils import sysconfig
from vext import open_spec

def add_vext(vext_file):
    """
    Create an entry for 'setup.py': 'data_files' that will
    install a vext
    """
    dest_dir = os.path.join(sysconfig.get_python_lib(), 'vext/specs')
    return (dest_dir, [vext_file])


def check_sysdeps(*vext_files):
    """
    Check that imports in 'test_imports' succeed
    otherwise display message in 'install_hints'
    """
    for vext_file in vext_files:
        success = True
        with open(vext_file) as f:
            vext = open_spec(f)
            install_hint = " ".join(vext.get('install_hints', ['System dependencies not found']))
            for m in vext.get('test_import', ''):
                try:
                    if m:
                        __import__(m)
                except ImportError:
                    print(install_hint)
                    success = False
                    break
    return success


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

