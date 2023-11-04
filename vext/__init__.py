import logging

import sysconfig
from os import environ
from os.path import join

VEXT_DEBUG_LOG = "VEXT_DEBUG_LOG"
vext_pth = join(sysconfig.get_path('purelib'), 'vext_importer.pth')

logger = logging.getLogger("vext")
if VEXT_DEBUG_LOG in environ and environ.get(VEXT_DEBUG_LOG, "0") == "1":
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
else:
    logger.setLevel(logging.ERROR) # don't output warnings unless debugging is enabled
    logger.addHandler(logging.NullHandler())


def install_importer():
    # This is here so that older versions of vext don't break.
    logger.warning("install_importer has been moved to gatekeeper module")
    from vext import gatekeeper
    gatekeeper.install_importer()
