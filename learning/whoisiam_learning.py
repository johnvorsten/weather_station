# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 06:49:15 2020

@author: z003vrzk
"""

#!/usr/bin/env python

"""
This application presents a 'console' prompt to the user asking for Who-Is and I-Am
commands which create the related APDUs, then lines up the coorresponding I-Am
for incoming traffic and prints out the contents.
"""
# Python imports
import sys, configparser

# Third party imports
"""Debugging is brought through a decorator ModuleLogger
ConfigArgumentParser grabs arguments from command line
the core.run function is required to communicate on a network"""
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd
from bacpypes.core import run, deferred, enable_sleeping
from bacpypes.iocb import IOCB
"""Protocol data units and application protocol data units"""
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import WhoIsRequest, IAmRequest
from bacpypes.errors import DecodingError
"""Create a simple application and local device instance"""
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# Keys
config_path = r"C:\Users\z003vrzk\.spyder-py3\Scripts\weather_station\config.ini"
config = configparser.ConfigParser()
config.read(config_path)
assert 'bacnet_client' in config.sections()

# some debugging
_debug = 1
_log = ModuleLogger(globals())

#%%

@bacpypes_debugging
class WhoIsIAmApplication(BIPSimpleApplication):
    whois_counter = {}
    iam_counter = {}

    def __init__(self, *args):
        if _debug: WhoIsIAmApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # keep track of requests to line up responses
        self._request = None

    def process_io(self, iocb):
        if _debug: WhoIsIAmApplication._debug("process_io %r", iocb)

        # save a copy of the request
        self._request = iocb.args[0]

        # forward it along
        BIPSimpleApplication.process_io(self, iocb)

    def confirmation(self, apdu):
        if _debug: WhoIsIAmApplication._debug("confirmation %r", apdu)

        # forward it along
        BIPSimpleApplication.confirmation(self, apdu)

    def indication(self, apdu):
        if _debug: WhoIsIAmApplication._debug("indication %r", apdu)

        if (isinstance(self._request, WhoIsRequest)) and (isinstance(apdu, IAmRequest)):
            device_type, device_instance = apdu.iAmDeviceIdentifier
            if device_type != 'device':
                raise DecodingError("invalid object type")

            if (self._request.deviceInstanceRangeLowLimit is not None) and \
                    (device_instance < self._request.deviceInstanceRangeLowLimit):
                pass
            elif (self._request.deviceInstanceRangeHighLimit is not None) and \
                    (device_instance > self._request.deviceInstanceRangeHighLimit):
                pass
            else:
                # print out the contents
                sys.stdout.write('pduSource = ' + repr(apdu.pduSource) + '\n')
                sys.stdout.write('iAmDeviceIdentifier = ' + str(apdu.iAmDeviceIdentifier) + '\n')
                sys.stdout.write('maxAPDULengthAccepted = ' + str(apdu.maxAPDULengthAccepted) + '\n')
                sys.stdout.write('segmentationSupported = ' + str(apdu.segmentationSupported) + '\n')
                sys.stdout.write('vendorID = ' + str(apdu.vendorID) + '\n')
                sys.stdout.flush()

        # forward it along
        BIPSimpleApplication.indication(self, apdu)


    def do_whois(self, address=None, lowlimit=None, highlimit=None):
        """whois [ <addr>] [ <lolimit> <hilimit> ]"""

        if _debug: self._debug("do_whois %r", (address, lowlimit, highlimit))

        try:
            # build a request
            request = WhoIsRequest()
            if address != None:
                request.pduDestination = Address(address)
            else:
                request.pduDestination = GlobalBroadcast()

            if address == None and isinstance(lowlimit, int) and isinstance(highlimit(int)):
                request.deviceInstanceRangeLowLimit = int(lowlimit)
                request.deviceInstanceRangeHighLimit = int(highlimit)
            if _debug: self._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: self._debug("    - iocb: %r", iocb)

            # give it to the application
            self.request_io(iocb)

            # build a key from the source and parameters
            key = (str(request.pduSource),
                request.deviceInstanceRangeLowLimit,
                request.deviceInstanceRangeHighLimit,
                )
            try:
                self.whois_counter[key] += 1
            except KeyError:
                self.whois_counter[key] = 1

        except Exception as err:
            self._exception("exception: %r", err)


    def do_iam(self, args):
        """iam"""
        args = args.split()
        if _debug: self._debug("do_iam %r", args)

        try:
            # build a request
            request = IAmRequest()
            request.pduDestination = GlobalBroadcast()

            # set the parameters from the device object
            request.iAmDeviceIdentifier = self.objectIdentifier
            request.maxAPDULengthAccepted = self.maxApduLengthAccepted
            request.segmentationSupported = self.segmentationSupported
            request.vendorID = self.vendorIdentifier
            if _debug: self._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: self._debug("    - iocb: %r", iocb)

            # give it to the application
            self.request_io(iocb)

            # build a key from the source, just use the instance number
            # Cache the key
            key = (str(request.pduSource),
                request.iAmDeviceIdentifier[1],
                )
            try:
                self.iam_counter[key] += 1
            except KeyError:
                self.iam_counter[key] = 1

        except Exception as err:
            self._exception("exception: %r", err)


    def do_rtn(self, args):
        """rtn <addr> <net> ... """
        args = args.split()
        if _debug: self._debug("do_rtn %r", args)

        # provide the address and a list of network numbers
        router_address = Address(args[0])
        network_list = [int(arg) for arg in args[1:]]

        # pass along to the service access point
        self.nsap.update_router_references(None, router_address, network_list)


#%%
def main():

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", config['bacnet_client'])

    # make a device object
    local_device = LocalDeviceObject(
        objectName=config['bacnet_client']['objectName'],
        objectIdentifier=int(config['bacnet_client']['objectIdentifier']),
        maxApduLengthAccepted=int(config['bacnet_client']['maxApduLengthAccepted']),
        segmentationSupported=config['bacnet_client']['segmentationSupported'],
        vendorIdentifier=int(config['bacnet_client']['vendorIdentifier']),
        )

    # make a sample application
    local_application = WhoIsIAmApplication(local_device, config['bacnet_client']['address'])
    # Emit who is request from application
    local_application.do_whois() # Implemented here
    local_application.who_is() # Inheirited

    # Destroy application and unbind socket
    # local_application.mux.directPort.handle_close()

    _log.debug("running")

    run()

    _log.debug("fini")

    print("----- Who Is -----")
    whois_counter = local_application.whois_counter
    for (src, lowlim, hilim), count in sorted(whois_counter.items()):
        print("%-20s %8s %8s %4d" % (src, lowlim, hilim, count))
    print("")

    print("----- I Am -----")
    iam_counter = local_application.iam_counter
    for (src, devid), count in sorted(iam_counter.items()):
        print("%-20s %8d %4d" % (src, devid, count))
    print("")



#%%
if __name__ == "__main__":
    main()
