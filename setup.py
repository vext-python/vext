from distutils import sysconfig
from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from setuptools.command import install_lib
from codecs import open  # To use a consistent encoding
from os import environ, path, unlink
from glob import glob
from shutil import copyfile
from sys import argv

here = path.abspath(path.dirname(__file__))
site_packages_path = sysconfig.get_python_lib()

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='vext',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.4',

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
    packages=['vext', 'vext.registry', 'vext.install'],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=["pyyaml==3.11"],

    # Install the import hook    
    data_files=[
        (site_packages_path, ["vext_importer.pth"] if environ.get('VIRTUAL_ENV') else []),
    ],

)
