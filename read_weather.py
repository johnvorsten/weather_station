# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 19:24:25 2020

@author: z003vrzk
"""

# Python imports
import configparser
import sys

# Third party imports
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# Local imports

# Debugging
_debug = 1
_log = ModuleLogger(globals())

# Keys
config_path = r"C:\Users\z003vrzk\.spyder-py3\Scripts\weather_station\config.ini"
config = configparser.ConfigParser()
config.read(config_path)
msg='section bacnet_client must be in .ini file'
assert 'bacnet_client' in config.sections(), msg
if _debug:
    objectName = config['bacnet_client']['objectName']
    address = config['bacnet_client']['address']
    objectIdentifier = config['bacnet_client']['objectIdentifier']
    maxApduLengthAccepted = config['bacnet_client']['maxApduLengthAccepted']
    segmentationSupported = config['bacnet_client']['segmentationSupported']
    maxSegmentsAccepted = config['bacnet_client']['maxSegmentsAccepted']
    vendorIdentifier = config['bacnet_client']['vendorIdentifier']
    foreignPort = config['bacnet_client']['foreignPort']
    foreignBBMD = config['bacnet_client']['foreignBBMD']
    foreignTTL = config['bacnet_client']['foreignTTL']

    for key, val in config['bacnet_client'].items():
        sys.stdout.write(key + ': ' + val + '\n')



#%%

"""
This sample application is the simplest BACpypes application that is
a complete stack.  Using an INI file it will configure a
LocalDeviceObject, create a SampleApplication instance, and run,
waiting for a keyboard interrupt or a TERM signal to quit.
"""


@bacpypes_debugging
class SampleApplication(BIPSimpleApplication):

    def __init__(self, device, address):
        if _debug: SampleApplication._debug("__init__ %r %r", device, address)
        BIPSimpleApplication.__init__(self, device, address)
        return None

    def request(self, apdu):
        if _debug: SampleApplication._debug("request %r", apdu)
        BIPSimpleApplication.request(self, apdu)
        return None

    def indication(self, apdu):
        if _debug: SampleApplication._debug("indication %r", apdu)
        BIPSimpleApplication.indication(self, apdu)
        return None

    def response(self, apdu):
        if _debug: SampleApplication._debug("response %r", apdu)
        BIPSimpleApplication.response(self, apdu)
        return None

    def confirmation(self, apdu):
        if _debug: SampleApplication._debug("confirmation %r", apdu)
        BIPSimpleApplication.confirmation(self, apdu)
        return None


def main():
    # parse the command line arguments and initialize loggers
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    local_device = LocalDeviceObject(
        objectName=config['bacnet_client']['objectName'],
        objectIdentifier=int(config['bacnet_client']['objectIdentifier']),
        maxApduLengthAccepted=int(config['bacnet_client']['maxApduLengthAccepted']),
        segmentationSupported=config['bacnet_client']['segmentationSupported'],
        vendorIdentifier=int(config['bacnet_client']['vendorIdentifier']),
        )

    # make a sample application
    local_application = SampleApplication(local_device, config['bacnet_client']['address'])
    if _debug: _log.debug("    - this_application: %r", local_application)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()