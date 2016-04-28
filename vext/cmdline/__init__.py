from __future__ import print_function
import os
import re
import sys

from os.path import basename, join
from vext import vext_pth
from vext.env import in_venv
from vext.install import install_vexts, create_pth
import vext.gatekeeper

def requires_venv(f):
    def run():
        if not in_venv():
            print("Must run inside virtualenv to %s vext." % f.__name__)
            sys.exit(1)
        else:
            f()

    return run


def list_vexts():
    from vext.gatekeeper import spec_files

    for fn in spec_files():
        print(os.path.basename(fn))


@requires_venv
def do_enable():
    """
    Uncomment any lines that start with #import in the .pth file
    """
    try:
        _lines = []
        with open(vext_pth, mode='r') as f:
            for line in f.readlines():
                if line.startswith('#') and line[1:].lstrip().startswith('import '):
                    _lines.append(line[1:].lstrip())
                else:
                    _lines.append(line)

        try:
            os.unlink('%s.tmp' % vext_pth)
        except:
            pass

        with open('%s.tmp' % vext_pth, mode='w+') as f:
            f.writelines(_lines)

        try:
            os.unlink('%s~' % vext_pth)
        except:
            pass

        os.rename(vext_pth, '%s~' % vext_pth)
        os.rename('%s.tmp' % vext_pth, vext_pth)
    except IOError as e:
        if e.errno == 2:
            # vext file doesn't exist, recreate it.
            create_pth()

@requires_venv
def do_disable():
    """
    Comment any lines that start with import in the .pth file
    """
    from vext import vext_pth

    try:
        _lines = []
        with open(vext_pth, mode='r') as f:
            for line in f.readlines():
                if not line.startswith('#') and line.startswith('import '):
                    _lines.append('# %s' % line)
                else:
                    _lines.append(line)

        try:
            os.unlink('%s.tmp' % vext_pth)
        except:
            pass

        with open('%s.tmp' % vext_pth, mode='w+') as f:
            f.writelines(_lines)

        try:
            os.unlink('%s~' % vext_pth)
        except:
            pass

        os.rename(vext_pth, '%s~' % vext_pth)
        os.rename('%s.tmp' % vext_pth, vext_pth)
    except IOError as e:
        if e.errno == 2:  # file didn't exist == disabled
            return


def do_status():
    from vext.gatekeeper import GatekeeperFinder

    if GatekeeperFinder.PATH_TRIGGER in sys.path:
        enabled_msg = 'enabled'
    else:
        enabled_msg = 'disabled'

    if in_venv():
        print('Running in virtualenv [%s]' % enabled_msg)
    else:
        print('Not running in virtualenv [%s]' % enabled_msg)


def do_check(vext_files):
    """
    Attempt to import everything in the 'test-imports' section of specified
    vext_files

    :param: list of vext filenames (without paths), '*' matches all.
    :return: True if test_imports was successful from all files
    """
    import vext
    # not efficient ... but then there shouldn't be many of these

    all_specs = set(vext.gatekeeper.spec_files_flat())
    if vext_files == ['*']:
        vext_files = all_specs
    unknown_specs = set(vext_files) - all_specs
    for fn in unknown_specs:
        print("%s is not an installed vext file." % fn, file=sys.stderr)

    if unknown_specs:
        return False

    check_passed = True
    for fn in [join(vext.gatekeeper.spec_dir(), fn) for fn in vext_files]:
        f = vext.gatekeeper.open_spec(open(fn))
        modules = f.get('test_import', [])
        for success, module in vext.gatekeeper.test_imports(modules):
            if not success:
                check_passed = False
            line = "import %s: %s" % (module, '[success]' if success else '[failed]')
            print(line)
        print('')

    return check_passed


def do_install_vexts(vext_files):
    for src, dst in install_vexts(vext_files):
        print("  %s" % src)


# def do_diagnose(vext_files):
#     # Try and find out minimal paths needed for
#     for

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Access system python modules from virtualenv.')
    parser.add_argument('-l', '--list', dest='list', action='store_true', help='List installed external packages')
    parser.add_argument('-e', '--enable', dest='enable', action='store_true', help='Disable Vext loader')
    parser.add_argument('-d', '--disable', dest='disable', action='store_true', help='Enable Vext loader')
    parser.add_argument('-s', '--status', dest='status', action='store_true', help='Show Vext status')
    parser.add_argument('-c', '--check', dest='check', nargs='*', help='[external package] Test imports for external package')
    # parser.add_argument('-g', '--diagnose', dest='check', nargs='*', help='[vext file]')
    # parser.add_argument('-u', '--unblock', dest='unblock', action='store', help='attempt to unblock module')  # TODO

    parser.add_argument('-i', '--install', dest='install', nargs='*', help='Install vext file (used during setup)')

    args = parser.parse_args()
    err_level = 0

    if args.list:
        do_status()
        list_vexts()
    if args.disable:
        do_disable()
    if args.enable:
        do_enable()
    if args.status:
        do_status()
    if args.check:
        if not do_check(args.check):
            err_level = 1
    #if args.diagnose:
    #    do_diagnose()
    if args.install:
        do_install_vexts(args.install)

    #else:
    #    do_status()
    #    print()
    #    parser.print_help()
    sys.exit(err_level)
