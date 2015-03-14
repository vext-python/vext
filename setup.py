import os

from distutils import sysconfig
from distutils.command.install_data import install_data
from setuptools import setup, sandbox
from setuptools import setup
#from setuptools.sandbox import DirectorySandbox

here = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

site_packages_path = sysconfig.get_python_lib()
site_packages_files = ["vext_importer.pth"] if os.environ.get('VIRTUAL_ENV') else []
## sandbox._EXCEPTIONS.extend(os.path.join(site_packages_path, f) for f in site_packages_files)

long_description=open('DESCRIPTION.rst').read()


# Monkey patch sandbox to allow installing of vext_importer
_old_ok = sandbox.DirectorySandbox._ok
def patched_ok(self, path):
    if path in site_packages_files:
        return True
    else:
        return _old_ok(self, path)
sandbox.DirectorySandbox._ok = patched_ok

class vext_install_data(install_data):
    # Make sure file is installed to sitepackages root on win32
    def finalize_options(self):
        """
        On win32 the files here are changed to '' which
        ends up inside the .egg, change this back to the
        absolute path.
        """
        global site_packages_files

        install_data.finalize_options(self)
        if os.name == 'nt':
            for i, f in enumerate(list(self.distribution.data_files)):
                if not isinstance(f, basestring):
                    folder, files = f
                    if files == site_packages_files:
                        # Replace with absolute path version
                        self.distribution.data_files[i] = (site_packages_path, files)


setup(
    cmdclass={'vext_install_data': vext_install_data},
    name='vext',
    version='0.2.7',

    description='Use system python packages in a virtualenv',
    long_description=long_description,
    url='https://github.com/stuaxo/vext',
    author='Stuart Axon',
    author_email='stuaxo2@yahoo.com',
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
    keywords='setuptools development',
    packages=['vext', 'vext.registry', 'vext.install', 'vext.cmdline'],

    install_requires=["pyyaml==3.11", "setuptools>=14.0"],

    # Install the import hook
    data_files=[
        (site_packages_path, site_packages_files),
    ],

    entry_points = {
            'console_scripts': [
                'vext = vext.cmdline:main'
            ]
        },
)

