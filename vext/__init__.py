import logging

from os import environ
from os.path import join
from distutils.sysconfig import get_python_lib

if environ.get("VEXT_DEBUG_LOG", "0") == "1":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)
    
vext_pth = join(get_python_lib(), 'vext_importer.pth')

logger = logging.getLogger("vext")

def install_importer():
    logger.debug("install_importer has been moved to gatekeeper module")
    from vext import gatekeeper
    gatekeeper.install_importer()
