from distutils import sysconfig
from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from setuptools.command import install_lib
from codecs import open  # To use a consistent encoding
from os import path, unlink
from glob import glob
from shutil import copyfile
from sys import argv

here = path.abspath(path.dirname(__file__))
site_packages_path = sysconfig.get_python_lib()

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

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
        if 'uninstall' in argv:
            dest=path.join(site_packages_path, 'vext_importer.pth')
            try:
                unlink(dest)
            except:            
                pass
            return []
        return install_lib.install_lib.install(self)


setup(
    name='vext',

    # Customise actions
    cmdclass={
        'install_lib': VextInstallLib,
        'uninstall': VextInstallLib 
        },

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.1',

    description='Use system python packages in a virtualenv',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/stuaxo/vext',

    # Author details
    author='Stuart Axon',
    author_email='stuaxo2@yahoo.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='sample setuptools development',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['vext', 'vext.syspy'],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=["pyyaml"],

    # List additional groups of dependencies here (e.g. development dependencies).
    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    #extras_require = {
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    #},

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    #package_data={
    #    'sample': ['package_data.dat'],
    #},

    # Add the import hook
    data_files=[
        (site_packages_path, ["vext_importer.pth"]),
        (path.join(site_packages_path, 'vext/specs'), glob('vext/specs/*.vext'))
        ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'vext=vext:main',
        ],
    },
)

#print (site_packages_path, ["vext_importer.pth"])