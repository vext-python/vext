from __future__ import print_function
import os
import re
import sys

def list_vexts():
    from vext import spec_files
    for fn in spec_files():
        print(os.path.basename(fn))

def enable():
    from vext import vext_pth
    _lines = []
    with open(vext_pth, mode='r') as f:
        for line in f.readlines():
            if line.startswith('#') and line[1:].lstrip().startswith('import '):
                _lines.append( line[1:].lstrip() )
            else:
                _lines.append( line )
    
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

def disable():
    from vext import vext_pth
    _lines = []
    with open(vext_pth, mode='r') as f:
        for line in f.readlines():
            if not line.startswith('#') and line.startswith('import '):
                _lines.append( '# %s' % line )
            else:
                _lines.append( line )

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

def status():
    from vext import GatekeeperFinder
    if GatekeeperFinder.PATH_TRIGGER in sys.path:
        enabled_msg = 'enabled'
    else:
        enabled_msg = 'disabled'
    
    if os.environ['VIRTUAL_ENV']:
        print('Running in virtualenv [%s]' % enabled_msg)
    else:
        print('Not running in virtualenv [%s]' % enabled_msg)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Access system python modules from virtualenv.')
    parser.add_argument('-l', '--list', dest='list', action='store_true', help='List external packages "Vext"')
    parser.add_argument('-e', '--enable', dest='enable', action='store_true', help='Disable Vext loader')
    parser.add_argument('-d', '--disable', dest='disable', action='store_true', help='Enable Vext loader')
    parser.add_argument('-s', '--status', dest='status', action='store_true', help='Show Vext status')
    parser.add_argument('-u', '--unblock', dest='unblock', action='store', help='attempt to unblock module')

    args = parser.parse_args()

    if args.list:
        status()
        list_vexts()
    elif args.disable:
        disable()
    elif args.enable:
        enable()
    elif args.status:
        status()
    else:
        status()
        print()
        parser.print_help()

