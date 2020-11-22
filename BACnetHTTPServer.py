# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 19:44:45 2020

@author: z003vrzk
"""

#!/usr/bin/python

"""
HTTPServer
"""

# Python imports
import os
import threading
import json
import zlib
from collections import OrderedDict
import configparser
from urllib.parse import urlparse, parse_qs
from socketserver import ThreadingMixIn, TCPServer
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler

# Third party imports
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.core import run, deferred, stop
from bacpypes.iocb import IOCB
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import (ReadPropertyRequest, WhoIsRequest,
                           ReadPropertyMultipleRequest, PropertyIdentifier,
                           PropertyReference, ReadAccessSpecification,
                           ReadPropertyMultipleACK,)
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array
from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype
from bacpypes.local.device import LocalDeviceObject


# Initialization
# some debugging
_debug = True
_log = ModuleLogger(globals())

# settings
# parse the command line arguments
parser = ConfigArgumentParser(description=__doc__)
# add an option for the server host
parser.add_argument("--host", type=str, help="server host")
# add an option for the server port
parser.add_argument("--port", type=int, help="server port")
DEFAULT_CONFIG_PATH = r"./weather_config.ini"

# reference a simple application
this_application = None
server = None

# TODO
# Cache control heder?

# favorite icon
favicon = zlib.decompress(
    b'x\x9c\xab\x983\n\x90\x00\x00\x9b,\xa5\x01'
    )


#%%
#
#   HTTPRequestHandler
#


@bacpypes_debugging
class HTTPRequestHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(b"Content-Type", "text/html")
        self.end_headers()
        return None

    def do_GET(self):
        """
        Example
        http://localhost/read/adderss/analogValue:1
        http://localhost/read/<address>/<object type>:<object instance number>
        http://localhost/whois/<address>/<object type>:<object instance number>
        http://localhost/read/<address>/<object type>:<object instance number>/<property>
        Example
        http://localhost:8081/read/192.168.1.100/analogValue:0/presentValue"""
        if _debug:
            HTTPRequestHandler._debug("do_GET")
        global favicon

        # get the thread
        cur_thread = threading.current_thread()
        if _debug:
            HTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)

        # parse query data and params to find out what was passed
        parsed_params = urlparse(self.path)
        if _debug:
            HTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
        parsed_query = parse_qs(parsed_params.query)
        if _debug:
            HTTPRequestHandler._debug("    - parsed_query: %r", parsed_query)

        # find the pieces
        args = parsed_params.path.split("/")
        if _debug:
            HTTPRequestHandler._debug("    - args: %r", args)

        if args[1] == "read":
            self.send_response(202)
            self.do_read(args[2:])
        elif args[1] == "whois":
            self.send_response(202)
            self.do_whois(args[2:])
        elif args[1] == "readpropertymultiple":
            self.send_response(404)
            self.send_header(b"Content-Type", "text/plain")
            self.end_headers()
            msg = ("'readpropertymultiple' API request must be POST request")
            self.wfile.write(bytes(msg, 'utf-8'))
        elif args[1] == "favicon.ico":
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", len(favicon))
            self.end_headers()
            self.wfile.write(favicon)
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"'read' or 'whois' expected")

        return


    def do_POST(self):
        """
        Example
        """
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        body_json = json.loads(body.decode('utf-8'))

        # Print current thread for help
        cur_thread = threading.current_thread()

        # parse query data and params to find out what was passed
        parsed_params = urlparse(self.path)

        # find the pieces
        args = parsed_params.path.split("/")

        if _debug:
            HTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
            HTTPRequestHandler._debug("    - args: %r", args)
            HTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)
            HTTPRequestHandler._debug("    - body_json: %r", body_json)
            HTTPRequestHandler._debug("    - path: %r", self.path)
            HTTPRequestHandler._debug("    - headers: %r", self.headers)

        if args[1] == "readpropertymultiple":
            self.send_response(202)
            self.do_ReadPropertyMultiple(args, body_json)

        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"'readpropertymultiple' expected from POST request")

        return


    def do_read(self, args):

        if _debug:
            HTTPRequestHandler._debug("do_read %r", args)

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
                HTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            timeout = int(self.headers.get('X-bacnet-timeout', 5))
            iocb.set_timeout(timeout, err=TimeoutError)
            if _debug:
                HTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # Wait for it to complete
            iocb.wait()

            # filter out errors and aborts
            if iocb.ioError:
                if _debug:
                    HTTPRequestHandler._debug("    - error: %r", iocb.ioError)
                result = {"error": str(iocb.ioError)}
            else:
                if _debug:
                    HTTPRequestHandler._debug(
                        "    - response: %r", iocb.ioResponse
                    )
                apdu = iocb.ioResponse

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    HTTPRequestHandler._debug("    - datatype: %r", datatype)
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
                        HTTPRequestHandler._debug(
                            "    - datatype: %r", datatype
                        )

                # convert the value to a dict if possible
                value = apdu.propertyValue.cast_out(datatype)
                if hasattr(value, "dict_contents"):
                    value = value.dict_contents(as_class=OrderedDict)
                if _debug:
                    HTTPRequestHandler._debug("    - value: %r", value)

                result = {"value": value}

        except Exception as err:
            HTTPRequestHandler._exception("exception: %r", err)
            result = {"exception": str(err)}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.send_header('Content-Type', 'Application/json')
        self.end_headers()
        self.wfile.write(result_bytes)


    def do_whois(self, args):

        NOT_IMPLEMENTED = True
        if NOT_IMPLEMENTED:
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(NotImplementedError('WhoIs not implemented'))
            return

        if _debug:
            HTTPRequestHandler._debug("do_whois %r", args)

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
                HTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            timeout = int(self.headers.get('X-bacnet-timeout', 5))
            iocb.set_timeout(timeout, err=TimeoutError)
            if _debug:
                HTTPRequestHandler._debug("    - iocb: %r", iocb)

            # Give it to the application
            deferred(this_application.request_io, iocb)
            iocb.wait()

            if iocb.ioError:
                if _debug:
                    HTTPRequestHandler._debug("    - error: %r", iocb.ioError)
                result = {"error": str(iocb.ioError)}

            else:
                if _debug:
                    HTTPRequestHandler._debug(
                        "    - response: %r", iocb.ioResponse
                    )
                apdu = iocb.ioResponse

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    HTTPRequestHandler._debug("    - datatype: %r", datatype)
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
                        HTTPRequestHandler._debug(
                            "    - datatype: %r", datatype
                        )

                # convert the value to a dict if possible
                value = apdu.propertyValue.cast_out(datatype)
                if hasattr(value, "dict_contents"):
                    value = value.dict_contents(as_class=OrderedDict)
                if _debug:
                    HTTPRequestHandler._debug("    - value: %r", value)

                result = {"value": value}

        except Exception as err:
            HTTPRequestHandler._exception("exception: %r", err)
            result = {"exception": str(err)}
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            result_bytes = json.dumps(result).encode("utf-8")
            self.wfile.write(result_bytes)
            return

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(result_bytes)
        return

    def _form_ReadPropertyMultiple_request(self, args, body_json):
        """
        Example Read
        http://localhost/read/adderss/analogValue:1
        http://localhost/read/<address>/<object type>:<object instance number>
        http://localhost/read/<address>/<object type>:<object instance number>/<property>
        http://localhost:8081/read/192.168.1.100/analogValue:0/presentValue

        Example WhoIs
        http://localhost/whois/<address>

        Example ReadPropertyMultiple
        http://localhost:8081/readpropertymultiple/<address>/

        body_json = {'address':'192.168.1.100',
                'bacnet_objects': [{'object': 'analogValue:1',
                                    'property': 'presentValue'},
                                   {'object': 'analogValue:2',
                                    'property': 'presentValue'},
                                   {'object': 'analogValue:3',
                                    'property': 'presentValue'}]}
        """
        # Error check request
        if body_json['bacnet_objects'].__len__() == 0:
            # No objects defined in list
            msg = ('No BACnet object specifiers were passed. '+
                   'Must include specifiers like {"object":"analogValue:1",' +
                   '"property":"presentValue"}'
                   )
            if _debug:
                HTTPRequestHandler._debug("    - body_json: %r", msg)
            self.send_header('Content-Type','text/plain')
            self.end_headers()
            self.wfile.write(bytes(msg, 'utf-8'))
            raise ValueError(msg)

        if not 'bacnet_objects' in body_json.keys():
            # Improperty structured JSON request
            msg = ('Bad request format. "bacnet_objects" must be a key '+
                   'in the request body JSON oject. Got {}'.format(str(body_json.keys()))
                   )
            if _debug:
                HTTPRequestHandler._debug("    - body_json: %r", msg)
            self.send_header('Content-Type','text/plain')
            self.end_headers()
            self.wfile.write(bytes(msg, 'utf-8'))
            raise ValueError(msg)

        # Build Read Access Spec List
        read_access_spec_list = []
        """Formatted like
        results = {'analogValue:1' : {'presentValue':'1',
                                      'objectName':'some_name',
                                      'arrayResult':[1,2,3]},
                   'analogValue:2' : {'presentValue':'4'}
                   }"""

        for bacnet_object in body_json['bacnet_objects']:

            # Property reference list (for EACH object being requested)
            prop_reference_list = []
            try:
                # What is the object identifier?
                obj_id = ObjectIdentifier(bacnet_object['object']).value
                # Get the object type
                if not get_object_class(obj_id[0]):
                    # The passed value is not a valid BACnet object type
                    msg = ('The requested Object Identifier is not a valid BACnet '+
                           'object type. Got {}'.format(str(obj_id))
                           )
                    if _debug:
                        HTTPRequestHandler._debug("    - obj_id: %r", msg)
                    self.send_header('Content-Type','text/plain')
                    self.end_headers()
                    self.wfile.write(bytes(msg, 'utf-8'))
                    raise ValueError(msg)
            except ValueError:
                # The passed value is not a valid BACnet object type
                msg = ('The requested Object Identifier is not a valid BACnet '+
                       'object type. Got {}'.format(str(obj_id))
                       )
                if _debug:
                    HTTPRequestHandler._debug("    - objectID: %r", msg)
                self.send_header('Content-Type','text/plain')
                self.end_headers()
                self.wfile.write(bytes(msg, 'utf-8'))
                raise ValueError(msg)

            # Property ID
            prop_id = bacnet_object['property']
            if prop_id not in PropertyIdentifier.enumerations:
                # Invalid property identifier - usually 'presentValue' or 'all'
                msg = ('Invalid BACnet property. Valid propery must be one of '+
                       '{}'.format(str(PropertyIdentifier.enumerations.keys()))
                       )
                if _debug:
                    HTTPRequestHandler._debug("    - bac property: %r", msg)
                self.send_header('Content-Type','text/plain')
                self.end_headers()
                self.wfile.write(bytes(msg, 'utf-8'))
                raise ValueError(msg)

            # Object datatype
            datatype = get_datatype(obj_id[0], prop_id)
            if (datatype is None) and (prop_id != 'all'):
                # For converting between BACnet data types and pyton types
                msg = ('Invalid combination of BACnet object type and property ID '+
                       'Got {}, {}'.format(str(obj_id), str(prop_id))
                       )
                if _debug:
                    HTTPRequestHandler._debug("    - datatype: %r", msg)
                self.send_header('Content-Type','text/plain')
                self.end_headers()
                self.wfile.write(bytes(msg, 'utf-8'))
                raise ValueError(msg)

            # Build property reference
            # Not sure what this is - check ASHRAE standard lol
            prop_reference = PropertyReference(propertyIdentifier=prop_id)
            # Array index for BACnet objects with multiple values
            # Array index not supported for this API - just get the whole array
            prop_reference_list.append(prop_reference)

            # Build read access specification
            read_access_spec = ReadAccessSpecification(
                objectIdentifier=obj_id,
                listOfPropertyReferences=prop_reference_list
                )
            read_access_spec_list.append(read_access_spec)

        # Build request
        request = ReadPropertyMultipleRequest(
            listOfReadAccessSpecs=read_access_spec_list,
            )
        request.pduDestination = Address(body_json['address'])
        return request


    def do_ReadPropertyMultiple(self, args, body_json):
        """
        Example Read
        http://localhost/read/adderss/analogValue:1
        http://localhost/read/<address>/<object type>:<object instance number>
        http://localhost/read/<address>/<object type>:<object instance number>/<property>
        http://localhost:8081/read/192.168.1.100/analogValue:0/presentValue

        Example WhoIs
        http://localhost/whois/<address>

        Example ReadPropertyMultiple
        http://localhost:8081/readpropertymultiple/

        args = {'bacnet_objects': [{'object': 'analogInput:1', 'property': 'presentValue'},
                                   {'object': 'analogInput:4', 'property': 'presentValue'},
                                   {'object': 'analogInput:8', 'property': 'presentValue'},
                                   {'object': 'analogInput:12', 'property': 'presentValue'}],
                'address': '665002'}
        headers = {'Content-Type':'application/json'}
        res = requests.post(url, headers=headers,
                            data=json.dumps(body),
                            timeout=2)
        """
        # Init results JSON
        results = {}
        try:
            request = self._form_ReadPropertyMultiple_request(args, body_json)
        except ValueError as e:
            # Headers were already written
            if _debug:
                HTTPRequestHandler._debug("    - request: %r", str(e))
            self.send_header('Content-Type','text/plain')
            self.end_headers()
            self.wfile.write(str(e))
            self.wfile.write(b'End of response')
            return

        # Make IOControlBlock
        iocb = IOCB(request)
        timeout = int(self.headers.get('X-bacnet-timeout', 4))
        iocb.set_timeout(timeout, err=TimeoutError)
        # Give iocb to app
        deferred(this_application.request_io, iocb)
        # Wait for completion
        iocb.wait()

        """Format of the response
        ObjectIdentifier
            PropertyIdentifier : PropertyValue
        """

        # Success
        if iocb.ioResponse:
            apdu = iocb.ioResponse

            # Acknowledgement response
            if not isinstance(apdu, ReadPropertyMultipleACK):
                msg = ('Received improper read property multiple response. ' +
                       'The expected response type was an acknowledgement, ' +
                       'got {}'.format(str(type(apdu)))
                       )
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(bytes(msg, 'utf-8'))
                return

            # loop through the results
            for result in apdu.listOfReadAccessResults:
                # Object identifiers are top
                objectIdentifier = result.objectIdentifier
                results[str(objectIdentifier)] = {}

                for element in result.listOfResults:
                    # Properties and array elements of each object are bottom
                    propertyIdentifier = element.propertyIdentifier
                    propertyArrayIndex = element.propertyArrayIndex
                    readResult = element.readResult

                    if readResult.propertyAccessError:
                        results[str(objectIdentifier)][str(propertyIdentifier)] = \
                            readResult.propertyAccessError
                        continue # Skip this result

                    # Form the message response
                    propertyValue = readResult.propertyValue
                    dtype = get_datatype(objectIdentifier[0], propertyIdentifier)
                    if issubclass(dtype, Array) and (propertyArrayIndex is not None):
                        # The property value is an array of values
                        if propertyArrayIndex == 0:
                            # Result is the first index of array
                            # See http://kargs.net/BACnet/Foundations2015-Developer-Q-A.pdf
                            value = propertyValue.cast_out(Unsigned)
                        else:
                            # Cast BACnet array to python array with elements
                            # Matching the BACnet array subtype
                            # [BACint, BACint, BACint] -> [pyint, pyint, pyint]
                            value = propertyValue.cast_out(dtype.subtype)
                    else:
                        # The value is not an array (single value)
                        value = propertyValue.cast_out(dtype)

                    # Form response JSON object
                    """results = {'analogValue:1' : {'presentValue':'1',
                                                     'objectName':'some_name',
                                                     'arrayResult':[1,2,3]},
                                  'analogValue:2' : {'presentValue':'4'}
                                  }
                    """
                    results[str(objectIdentifier)][str(propertyIdentifier)] = value
        else:
            # Error
            msg = ('Received improper BACnet response \n' +
                   'args : {}\n' +
                   'kwargs : {}\n' +
                   'ioState : {}\n' +
                   'ioComplete : {}\n' +
                   'ioCallback : {}\n' +
                   'ioResponse : {}')
            msg = msg.format(iocb.args, iocb.kwargs,
                             iocb.ioState, iocb.ioComplete,
                             iocb.ioCallback, iocb.ioResponse)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(msg, 'utf-8'))
            return

        # Write the response
        try:
            msg = bytes(json.dumps(results), 'utf-8')
        except TypeError:
            # Cannot serialize value of results
            msg = bytes(json.dumps(results, default=lambda o: str(o)), 'utf-8')

        if _debug:
            HTTPRequestHandler._debug("    - response: %r", str(msg))
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(msg)

        return




class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


#
#   __main__
#

def main(child_thread=False):
    global this_application, server, server_thread, bac_thread

    try:

        # Parse command line arguments with ini file configuration
        # This Parser expects the default ini file path of ./BACpypes.ini
        # With a BACpypes section. If ./BACpypes.ini does not exist then pass
        # a different file under --ini
        args = parser.parse_args()

        if _debug:
            _log.debug("initialization")
            _log.debug("    - args: %r", args)

        # Make a device object
        this_device = LocalDeviceObject(ini=args.ini)

        # Make a simple application
        this_application = BIPSimpleApplication(this_device, args.ini.address)

        # local host, special port
        server = ThreadedTCPServer((args.host, args.port), HTTPRequestHandler)

        # Start a thread with the server -- that thread will then start a thread
        # for each request
        server_thread = threading.Thread(target=server.serve_forever)

        # exit the server thread when the main thread terminates
        server_thread.daemon = True # Exit when program terminates
        server_thread.start()

        if _debug:
            _log.debug("running")
            _log.debug("    - server_thread: %r", server_thread)
            _log.debug("    - server: %r", server)
            _log.debug("    - this_device: %r", this_device)

        if child_thread==True:
            # Start the BACnet application in a child thread
            # Child threads do not receive signals SIGTERM or SIGUSR1
            bac_thread = threading.Thread(target=run)
            bac_thread.daemon = False # Keep the thread open for interactive
            bac_thread.start()
        else:
            # Start the BACnet thread in the main thread
            # This blocks
            run()

    except Exception as err:
        _log.exception("an error has occurred: %s", err)

    finally:
        if server:
            server.shutdown()
        if this_application:
            # Close the port manually if needed
            this_application.mux.directPort.handle_close()
            stop()
        if _debug:
            _log.debug("finally")
    return


if __name__ == '__main__':
    """Begin BACnet client when this script is run as a top-level scope
    Example of top-level scope -
    python httpServer.py
    python -m httpServer.py

    Example - not executed as top-level
    from httpServer import main
    """
    main(child_thread=False)