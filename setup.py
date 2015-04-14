from glob import glob
from os.path import abspath, basename, dirname, join, normpath

from distutils import sysconfig
from distutils.command.build import build

from setuptools import setup
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

long_description=open('DESCRIPTION.rst').read()

setup(
    cmdclass={
        'build': BuildWithPTH,
        'easy_install': EasyInstallWithPTH,
        'develop': DevelopWithPTH,
    },

    name='vext',
    version='0.3.3',
    # We need to have a real directory not a zip file:
    zip_safe=False,

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
    #data_files=[
    #    (site_packages_path, site_packages_files),
    #],

    entry_points = {
            'console_scripts': [
                'vext = vext.cmdline:main'
            ]
        },
)
