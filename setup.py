from __future__ import print_function

import sys
import pkg_resources

from distutils.version import StrictVersion
from pkg_resources import DistributionNotFound

MIN_SETUPTOOLS = "18.0"

try:
    reload
except NameError:
    # python 3
    from imp import reload

def upgrade_setuptools():
    """ 
    setuptools 12.2 can trigger a really nasty bug
    that eats all memory, so upgrade it to
    14.1, which is known to be good.
    """
    # Note - I tried including the higher version in
    # setup_requires, but was still able to trigger
    # the bug. - stu.axon
    global MIN_SETUPTOOLS
    r = None
    try:
        r = pkg_resources.require(["setuptools"])[0]
    except DistributionNotFound:
        # ok, setuptools will be installed later
        return

    if StrictVersion(r.version) >= StrictVersion(MIN_SETUPTOOLS):
        return
    else:
        print("Upgrading setuptools...")
        subprocess.call("pip install 'setuptools>=%s'" % MIN_SETUPTOOLS, shell=True)


if "install" in sys.argv:
    upgrade_setuptools()
    reload(pkg_resources)
    try:
        r = pkg_resources.require(["setuptools"])[0]
        print("setuptools version: %s" % r.version)
    except DistributionNotFound:
        # ok, setuptools will be installed later
        print("setuptools not found.")
        sys.exit(1)

import subprocess

from glob import glob
from os.path import abspath, basename, dirname, join, normpath, relpath
from shutil import rmtree
from textwrap import dedent

from distutils.command.build import build

from setuptools import setup
from setuptools import Command
from setuptools.command.develop import develop
from setuptools.command.easy_install import easy_install

here = normpath(abspath(dirname(__file__)))


class BuildWithPTH(build):
    def run(self):
        build.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.build_lib, basename(path))
        self.copy_file(path, dest)


class EasyInstallWithPTH(easy_install):
    def run(self):
        easy_install.run(self)
        for path in glob(join(here, 'vext_importer.pth')):
            dest = join(self.install_dir, basename(path))
            self.copy_file(path, dest)


class DevelopWithPTH(develop):
    def run(self):
        develop.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info ./__pycache__'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob(normpath(join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % relpath(path))
                rmtree(path)


long_description = dedent("""
    Use system python packages in virtualenv (for packages that dont work in virtualenv).
""")

setup(
    cmdclass={
        'build': BuildWithPTH,
        'easy_install': EasyInstallWithPTH,
        'develop': DevelopWithPTH,
        'clean': CleanCommand,
    },

    name='vext',
    version='0.4.99',
    # We need to have a real directory not a zip file:
    zip_safe=False,

    description='Use system python packages from a virtualenv',
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
    packages=[
        'vext',
        'vext.cmdline',
        'vext.env',
        'vext.helpers',
        'vext.gatekeeper',
        'vext.registry',
        'vext.install',
    ],

    setup_requires=["setuptools>=18.0.1"],
    install_requires=["pyyaml==3.11"],

    # Install the import hook
    # data_files=[
    #    (site_packages_path, site_packages_files),
    # ],

    entry_points={
        'console_scripts': [
            'vext = vext.cmdline:main'
        ]
    },
)
