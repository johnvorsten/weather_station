# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 20:32:55 2020

@author: z003vrzk
"""


# Python imports
import unittest
import os
import threading
import json
import zlib
from collections import OrderedDict
import configparser
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn, TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

# Third party imports
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred, stop
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import ReadPropertyRequest, WhoIsRequest
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype
from bacpypes.local.device import LocalDeviceObject



#%%

class httpServerTest(unittest.TestCase):

    def setUp(self):

        # TODO this will not always be static
        # Default parameters for building requests
        # [BACpypes]
        client = {
            'objectName': 'weather_pi_10201',
            'address': '192.168.1.101/24',
            'objectIdentifier': '10201',
            'maxApduLengthAccepted': '1024',
            'segmentationSupported': 'segmentedBoth',
            'maxSegmentsAccepted': '1024',
            'vendorIdentifier': '70',
            'foreignPort': '0',
            'foreignBBMD': '128.253.109.254',
            'foreignTTL': '30',
            }

        # TODO Make this a server on this computer
        # Initialized without having to plug into the physical device
        # BACnet server device
        server = {
            'objectName': 'weatherpxc',
            'address': '192.168.1.100/24',
            'objectIdentifier': '10101',
            'maxApduLengthAccepted': '1024',
            'segmentationSupported': 'segmentedBoth',
            'maxSegmentsAccepted': '1024',
            'vendorIdentifier': '70',
            'foreignPort': '0',
            'foreignBBMD': '128.253.109.254',
            'foreignTTL': '30',}

        # TODO Create these on the the server object if it is made on a
        # Virtual device
        # Some server internal objects to test
        server_objects = {
            'OBJECT_ANALOG_INPUT:0':{
                'Object Name':'APT.AI1',
                },
            'OBJECT_ANALOG_VALUE:10000':
                {'Object Name':'!weatherpxc:Address'},
            'OBJECT_ANALOG_VALUE:10001':{
                'Object Name':'!weatherpxc:ALMCNT'}
            }


        return None

    def test_parse(self):
        path = 'http://localhost:8080/read/10101/1'
        cur_thread = threading.current_thread()
        print('Current Thread', cur_thread)

        parsed_params = urlparse(path)
        print('parsed parameters from URL', parsed_params)
        parsed_query = parse_qs(parsed_params.query)
        args = parsed_params.path.split("/")
        print('Parsed parameters from path', args)

        if args[1] == "read":
            print("Read request", args[1])
            print('Read call signature: self.do_read({})'.format(args[2:]))
            # Example
            # self.do_read(args[2:])
        elif args[1] == "whois":
            print("WhoIs request", args[1])
            print('WhoIs call signature: self.do_whois({})'.format(args[2:]))
            # Example
            # self.do_whois(args[2:])
        elif args[1] == "favicon.ico":
            print("favicon.ico request", args[1])
            # Example
            # self.send_response(200)
            # self.send_header("Content-type", "image/x-icon")
            # self.send_header("Content-Length", len(favicon))
            # self.end_headers()
            # self.wfile.write(favicon)
        else:
            # Invalid format
            print(str(
                # self.send_response(200)
                # self.send_header("Content-type", "text/plain")
                # self.end_headers()
                # self.wfile.write(b"'read' or 'whois' expected")
                ))

        return None

    def test_ObjectIdentifier(self):
        """Test valid inputs to ObjectIdentifier
        ObjectIdentifier(<object type>, <object instance number>)
        # Assume default object type
        ObjectIdentifier(<object instance number>) # Assumes default object type
        # Parse string
        ObjectIdentifier('<object type>:<object instance number>')
        """
        res = ObjectIdentifier(1).value # ('analogInput', 1)
        self.assertEqual(res[0], 'analogInput')
        self.assertEqual(res[1], 1)
        res = ObjectIdentifier('analogValue:1').value # ('analogValue', 1)
        self.assertEqual(res[0], 'analogValue')
        self.assertEqual(res[1], 1)
        res = ObjectIdentifier(2).value # ('analogInput', 2)
        self.assertEqual(res[0], 'analogInput')
        self.assertEqual(res[1], 2)
        res = ObjectIdentifier(5, 1).value # ('binaryValue', 1)
        self.assertEqual(res[0], 'binaryValue')
        self.assertEqual(res[1], 1)
        return None

    def test_do_read(self, read_args=('192.168.1.100', 'analogValue:1')):
        """inputs
        -------
        read_args : (iterable) of ('', 'read', address, object id)
            address : (int)
            object ID : (int)"""

        try:
            addr, obj_id = read_args[:2]
            obj_id = ObjectIdentifier(obj_id).value

            # get the object type
            if not get_object_class(obj_id[0]): # bacpypes.object.AnalogInputObject
                raise ValueError("unknown object type")

            # implement a default property, the bain of committee meetings
            if len(args) == 3:
                prop_id = args[2]
            else:
                prop_id = "presentValue"

            # look for its datatype, an easy way to see if the property is
            # appropriate for the object
            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id
            )
            request.pduDestination = Address(addr)

            # look for an optional array index
            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # filter out errors and aborts
            if iocb.ioError:
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - error: %r", iocb.ioError)
                result = {"error": str(iocb.ioError)}
            else:
                if _debug:
                    ThreadedHTTPRequestHandler._debug(
                        "    - response: %r", iocb.ioResponse
                    )
                apdu = iocb.ioResponse

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None
                ):
                    if apdu.propertyArrayIndex == 0:
                        datatype = Unsigned
                    else:
                        datatype = datatype.subtype
                    if _debug:
                        ThreadedHTTPRequestHandler._debug(
                            "    - datatype: %r", datatype
                        )

                # convert the value to a dict if possible
                value = apdu.propertyValue.cast_out(datatype)
                if hasattr(value, "dict_contents"):
                    value = value.dict_contents(as_class=OrderedDict)
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - value: %r", value)

                result = {"value": value}

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = {"exception": str(err)}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.wfile.write(result_bytes)
        return None















def do_GET(self):
    if _debug:
        ThreadedHTTPRequestHandler._debug("do_GET")
    global favicon

    # get the thread
    cur_thread = threading.current_thread()
    if _debug:
        ThreadedHTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)

    # parse query data and params to find out what was passed
    parsed_params = urlparse(self.path)
    if _debug:
        ThreadedHTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
    parsed_query = parse_qs(parsed_params.query)
    if _debug:
        ThreadedHTTPRequestHandler._debug("    - parsed_query: %r", parsed_query)

    # find the pieces
    args = parsed_params.path.split("/")
    if _debug:
        ThreadedHTTPRequestHandler._debug("    - args: %r", args)

    if args[1] == "read":
        self.do_read(args[2:])
    elif args[1] == "whois":
        self.do_whois(args[2:])
    elif args[1] == "favicon.ico":
        self.send_response(200)
        self.send_header("Content-type", "image/x-icon")
        self.send_header("Content-Length", len(favicon))
        self.end_headers()
        self.wfile.write(favicon)
    else:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"'read' or 'whois' expected")

def do_read(self, args):
    if _debug:
        ThreadedHTTPRequestHandler._debug("do_read %r", args)

    try:
        addr, obj_id = args[:2]
        obj_id = ObjectIdentifier(obj_id).value

        # get the object type
        if not get_object_class(obj_id[0]):
            raise ValueError("unknown object type")

        # implement a default property, the bain of committee meetings
        if len(args) == 3:
            prop_id = args[2]
        else:
            prop_id = "presentValue"

        # look for its datatype, an easy way to see if the property is
        # appropriate for the object
        datatype = get_datatype(obj_id[0], prop_id)
        if not datatype:
            raise ValueError("invalid property for object type")

        # build a request
        request = ReadPropertyRequest(
            objectIdentifier=obj_id, propertyIdentifier=prop_id
        )
        request.pduDestination = Address(addr)

        # look for an optional array index
        if len(args) == 5:
            request.propertyArrayIndex = int(args[4])
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

        # give it to the application
        deferred(this_application.request_io, iocb)

        # wait for it to complete
        iocb.wait()

        # filter out errors and aborts
        if iocb.ioError:
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - error: %r", iocb.ioError)
            result = {"error": str(iocb.ioError)}
        else:
            if _debug:
                ThreadedHTTPRequestHandler._debug(
                    "    - response: %r", iocb.ioResponse
                )
            apdu = iocb.ioResponse

            # find the datatype
            datatype = get_datatype(
                apdu.objectIdentifier[0], apdu.propertyIdentifier
            )
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (
                apdu.propertyArrayIndex is not None
            ):
                if apdu.propertyArrayIndex == 0:
                    datatype = Unsigned
                else:
                    datatype = datatype.subtype
                if _debug:
                    ThreadedHTTPRequestHandler._debug(
                        "    - datatype: %r", datatype
                    )

            # convert the value to a dict if possible
            value = apdu.propertyValue.cast_out(datatype)
            if hasattr(value, "dict_contents"):
                value = value.dict_contents(as_class=OrderedDict)
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - value: %r", value)

            result = {"value": value}

    except Exception as err:
        ThreadedHTTPRequestHandler._exception("exception: %r", err)
        result = {"exception": str(err)}

    # encode the results as JSON, convert to bytes
    result_bytes = json.dumps(result).encode("utf-8")

    # write the result
    self.wfile.write(result_bytes)

def do_whois(self, args):
    if _debug:
        ThreadedHTTPRequestHandler._debug("do_whois %r", args)

    try:
        # build a request
        request = WhoIsRequest()
        if (len(args) == 1) or (len(args) == 3):
            request.pduDestination = Address(args[0])
            del args[0]
        else:
            request.pduDestination = GlobalBroadcast()

        if len(args) == 2:
            request.deviceInstanceRangeLowLimit = int(args[0])
            request.deviceInstanceRangeHighLimit = int(args[1])
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

        # give it to the application
        this_application.request_io(iocb)

        # no result -- it would be nice if these were the matching I-Am's
        result = {}

    except Exception as err:
        ThreadedHTTPRequestHandler._exception("exception: %r", err)
        result = {"exception": str(err)}

    # encode the results as JSON, convert to bytes
    result_bytes = json.dumps(result).encode("utf-8")

    # write the result
    self.wfile.write(result_bytes)