from __future__ import print_function

import logging
import os
import pkg_resources
import subprocess
import sys

from distutils.version import StrictVersion
from pkg_resources import DistributionNotFound

if "VEXT_DEBUG_LOG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)

ignore_reload_errors = "VEXT_RELOAD_HACK" in os.environ
logger = logging.getLogger("vext")


MIN_SETUPTOOLS = "18.8"
os.environ['VEXT_DISABLED'] = '1'   # Hopefully this will prevent the nasty memleak that can happen.
version = "0.5.23"

try:
    reload
except NameError:
    # python 3
    from imp import reload

def upgrade_setuptools():
    """ 
    setuptools 12.2 can trigger a really nasty bug
    that eats all memory, so upgrade it to
    18.8, which is known to be good.
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


def do_reload(module):
    if ignore_reload_errors:
        try:
            reload(pkg_resources)
        except Exception as e:
            # Horrible hack to workaround travis problem
            print("VEXT_RELOAD_HACK set, ignoring %s" % e)
    else:
        reload(pkg_resources)

if "install" in sys.argv:
    upgrade_setuptools()
    do_reload(pkg_resources)
    try:
        r = pkg_resources.require(["setuptools"])[0]
        print("setuptools version: %s" % r.version)
    except DistributionNotFound:
        # ok, setuptools will be installed later
        print("setuptools not found.")
        sys.exit(1)

from glob import glob
from os.path import abspath, basename, dirname, join, normpath, relpath
from shutil import rmtree
from textwrap import dedent

from distutils.command.build import build

from setuptools import setup
from setuptools import Command
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.easy_install import easy_install
from setuptools.command.install_lib import install_lib

here = normpath(abspath(dirname(__file__)))


class BuildWithPTH(build):
    def run(self):
        build.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.build_lib, basename(path))
        self.copy_file(path, dest)

class InstallWithPTH(install):
    def run(self):
        install.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.install_lib, basename(path))
        self.copy_file(path, dest)

class EasyInstallWithPTH(easy_install):
    def run(self):
        easy_install.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)


class DevelopWithPTH(develop):
    def run(self):
        develop.run(self)
        path = join(here, 'vext_importer.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)


class InstallLib(install_lib):
    #
    # Next part is when run InstallLib is run - we need to go find
    # any packages that depend on vext that have been installed
    # before and install the .vext files they provide
    #
    def installed_packages(self):
        """ :return: list of installed packages """
        packages = []
        for package in subprocess.check_output(["pip", "freeze"]) \
                .decode('utf-8'). \
                splitlines():
            for comparator in ["==", ">=", "<=", "<", ">"]:
                if comparator in package:
                    # installed package names usually look like Pillow==2.8.1
                    # ignore others, like external packages that pip show
                    # won't understand
                    name = package.partition(comparator)[0]
                    packages.append(name)
        return packages

    def package_info(self):
        """
        :return: list of package info on installed packages
        """
        import subprocess
        # create a commandline like  pip show Pillow show
        package_names = self.installed_packages()
        if not package_names:
            # No installed packages yet, so nothign to do here...
            return []

        cmdline = ["pip"]
        for name in package_names:
            cmdline.extend(["show", name])

        output = subprocess.check_output(cmdline)
        # Python 3 fix
        if not isinstance(output, str):
            output = str(output, 'UTF-8')
        # parse output that looks like this example
        """
        ---
        Name: Pillow
        Version: 2.8.1
        Location: /mnt/data/home/stu/.virtualenvs/shoebot-setup/lib/python2.7/site-packages/Pillow-2.8.1-py2.7-linux-x86_64.egg
        Requires:
        ---
        Name: vext.gi
        Version: 0.5.6.25
        Location: /mnt/data/home/stu/.virtualenvs/shoebot-setup/lib/python2.7/site-packages/vext.gi-0.5.6.25-py2.7.egg
        Requires: vext

        """
        results = []
        for info in output[3:].split("---"):
            d = {}
            for line in info[1:].splitlines():
                arg, _, value = line.partition(': ')
                arg = arg.lower()
                if arg == 'requires':
                    value = value.split(', ')
                d[arg] = value
            results.append(d)
        return results

    def depends_on(self, dependency):
        """
        List of packages that depend on dependency
        :param dependency: package name, e.g.  'vext' or 'Pillow'
        """
        packages = self.package_info()
        return [package for package in packages if dependency in package.get("requires", "")]

    def find_vext_files(self):
        """
        :return:  Absolute paths to any provided vext files
        """
        packages = self.depends_on("vext")
        vext_files = []
        for location in [package.get("location") for package in packages]:
            if not location:
                continue
            vext_files.extend(glob(join(location, "*.vext")))
        return vext_files

    def manually_install_vext(self, vext_files):
        if vext_files:
            code = dedent("""
                from vext.install import install_vexts
                for status in install_vexts(%s, verify=False):
                    print(status)
            """ % vext_files)
            cmd = [sys.executable, '-c', code]
            output = subprocess.check_output(cmd)
            print(output)  # console spam

    def enable_vext(self):
        code = dedent("""
            from vext.install import create_pth
            create_pth()
        """)
        cmd = [sys.executable, '-c', code]
        print("Enable Vext...")
        output = subprocess.check_output(cmd)
        print(output) # console spam

    def run(self):
        """
        Need to find any pre-existing vext contained in dependent packages
        and install them

        example:

        you create a setup.py with install_requires["vext.gi"]:

        - vext.gi gets installed using bdist_egg
        - vext itself is now called with bdist_egg and we end up here

        Vext now needs to find and install .vext files in vext.gi
        [or any other files that depend on vext]

        :return:
        """
        print("vext InstallLib")

        # Find packages that depend on vext and check for .vext files...

        vext_files = self.find_vext_files()
        print("vext files: ", vext_files)
        self.manually_install_vext(vext_files)
        self.enable_vext()
        install_lib.run(self)


#
# - end of InstallLib code


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

setup(
    cmdclass={
        'build': BuildWithPTH,
        'easy_install': EasyInstallWithPTH,
        'install': InstallWithPTH,
        'install_lib': InstallLib,
        'develop': DevelopWithPTH,
        'clean': CleanCommand,
    },

    name='vext',
    version=version,
    # We need to have a real directory not a zip file:
    zip_safe=False,

    description='Use system python packages from a virtualenv',
    long_description=dedent("""
        Use specific system python packages from virtualenv without --system-site-packages.

        Supports:
        pygtk, gi (gtk3), qt4, qt5, panda3d, vtk, wx
        """),
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

    setup_requires=["setuptools>=18.0.1", "pip>=1.5.6"],
    install_requires=["ruamel.yaml>=0.11.10"],

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
