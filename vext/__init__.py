import logging
import sys

from os import environ
from os.path import join
from distutils.sysconfig import get_python_lib

VEXT_DEBUG_LOG = "VEXT_DEBUG_LOG"
vext_pth = join(get_python_lib(), 'vext_importer.pth')

logger = logging.getLogger("vext")
if VEXT_DEBUG_LOG in environ and environ.get(VEXT_DEBUG_LOG, "0") == "1":
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
else:
    logger.addHandler(logging.NullHandler())


def install_importer():
    # This is here so that older versions of vext don't break.
    logger.warning("install_importer has been moved to gatekeeper module")
    from vext import gatekeeper
    gatekeeper.install_importer()
