# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 20:32:55 2020

@author: z003vrzk
"""

# Python imports
import unittest
from urllib.parse import urlparse, parse_qs
import json
import threading
from queue import Queue, Empty
import time
import subprocess
import re

# Third party imports
import requests
from bacpypes.core import run, stop
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.iocb import IOCB
from bacpypes.pdu import Address
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.primitivedata import ObjectIdentifier
from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype
from bacpypes.local.device import LocalDeviceObject

# Local imports
from httpServer import HTTPRequestHandler, ThreadedTCPServer
import httpServer

# Globals & Declarations
process_queue = Queue()
ini_file = r"C:\Users\z003vrzk\.spyder-py3\Scripts\weather_station\bacnet_client.ini"
HOST, PORT = 'localhost','8083'
BAC_SERVER_ADDRESS = '192.168.1.100'

# Check if network interface is active
import subprocess
cmd = ['netsh','interface','show','interface']
process = subprocess.run(cmd, stdout=subprocess.PIPE)
"""
'Admin State    State          Type             Interface Name',
 '-------------------------------------------------------------------------',
 'Enabled        Connected      Dedicated        Wi-Fi'
 """
ADAPTER_ENABLED = False
ADAPTER_CONNECTED = False
for line in process.stdout.decode().split('\r\n'):
    if re.search('Ethernet', line):
        if re.search('Enabled', line):
            ADAPTER_ENABLED = True
        if re.search('Connected', line):
            ADAPTER_CONNECTED = True



#%%


class BacnetHTTPServerTest(unittest.TestCase):

    def setUp(self):
        global server, server_thread, this_application
        # parse the command line arguments
        parser = ConfigArgumentParser(description=__doc__)
        # add an option for the server host
        parser.add_argument("--host", type=str, help="server host", default=HOST)
        # add an option for the server port
        parser.add_argument("--port", type=int, help="server port", default=PORT)

        # Adding arguments to the argument parser
        config_path = "./bacnet_client.ini"
        args = parser.parse_args(['--ini', config_path])

        # Make a HTTP Server
        server = ThreadedTCPServer((args.host, args.port), HTTPRequestHandler)

        # Start a thread with the server -- that thread will then start a thread for each request
        server_thread = threading.Thread(target=server.serve_forever)

        # exit the server thread when the main thread terminates
        server_thread.daemon = True # Exit when program terminates
        server_thread.start()
        print("HTTP Server Thread is Alive : ", server_thread.is_alive())

        # Make a device object
        this_device = LocalDeviceObject(ini=args.ini)

        # Make a simple application
        this_application = BIPSimpleApplication(this_device, args.ini.address)
        httpServer.this_application = this_application

        # Start the BACnet application in a child thread
        # Child threads do not receive signals SIGTERM or SIGUSR1
        bac_thread = threading.Thread(target=run)
        bac_thread.daemon = True # Exit when program terminates
        bac_thread.start()
        print("BACnet client Thread is Alive : ", bac_thread.is_alive())

        return


    def tearDown(self):

        # Stop the HHTP Server
        # stop servce_forever loop and wait until it stops
        server.shutdown()
        # Clean up the server - Release socket
        server.server_close()

        # Stop the BACnet client
        # Close the port manually if needed
        stop()
        this_application.mux.directPort.handle_close()


    def test_POST_400(self):
        """General implementation of POST method -
        This does not test a specific API request
        Bad URI request"""
        url = 'http://{}:{}/bad-url/'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        bacnet_object1 = {'object':'analogValue:1',
                          'property':'presentValue'}
        bacnet_object2 = {'object':'analogValue:2',
                          'property':'presentValue'}
        bacnet_object3 = {'object':'analogValue:3',
                          'property':'presentValue'}
        body = {'bacnet_objects':[bacnet_object1, bacnet_object2, bacnet_object3],
                'address':'192.168.1.100'}

        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=2)
        test_content = b"'readpropertymultiple' expected from POST request"
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content, test_content)

        return


    def test_GET_400(self):
        """Bad URI request"""
        url = 'http://{}:{}/bad-url'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=2)
        test_content = b"'read' or 'whois' expected"
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.content, test_content)

        return


    def test_encode_json(self):
        bacnet_object1 = {'object':'analogValue:1',
                          'property':'presentValue'}
        bacnet_object2 = {'object':'analogValue:2',
                          'property':'presentValue'}
        bacnet_object3 = {'object':'analogValue:3',
                          'property':'presentValue'}
        body = {'bacnet_objects':[bacnet_object1, bacnet_object2, bacnet_object3],
                'address':'192.168.1.100'}

        # Incorrect - Form encoded (not JSON encoded)
        res2 = requests.post('https://httpbin.org/post', data=body, timeout=2)
        test2_dict = {'form': {'address': '192.168.1.100',
                               'bacnet_objects': ['object', 'property',
                                                  'object', 'property',
                                                  'object', 'property']}}
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()['form'], test2_dict['form'])

        # Correct - String JSON representation
        # The resulting json is actually a string (not dict)
        res3 = requests.post('https://httpbin.org/post', data=json.dumps(body), timeout=2)
        test3_dict = {'bacnet_objects': [{'object': 'analogValue:1', 'property': 'presentValue'},
                                         {'object': 'analogValue:2', 'property': 'presentValue'},
                                         {'object': 'analogValue:3', 'property': 'presentValue'}],
                      'address': '192.168.1.100'}
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(json.loads(res3.json()['data']), test3_dict)

        # Correct - pass python object with json keyword
        res4 = requests.post('https://httpbin.org/post', json=body, timeout=2)
        test4_dict = {'bacnet_objects': [{'object': 'analogValue:1', 'property': 'presentValue'},
                                         {'object': 'analogValue:2', 'property': 'presentValue'},
                                         {'object': 'analogValue:3', 'property': 'presentValue'}],
                      'address': '192.168.1.100'}
        self.assertEqual(res4.status_code, 200)
        self.assertEqual(json.loads(res4.json()['data']), test4_dict)

        return


    @unittest.skip("WhoIs method is not implemented in the HTTP server")
    def test_WHOIS(self):

        # Make some requests
        url = 'http://{}:{}/whois/192.168.1.100'.format(HOST,PORT)
        headers = {'X-bacnet-timeout':'3', 'Content-Type':'application/json'}
        res = requests.get(url, headers=headers, timeout=5)

        self.assertEqual(res.status_code, 202)

        return


    def test_READ(self):

        # Make some requests
        url = 'http://{}:{}/read/192.168.1.100/analogInput:0'.format(HOST,PORT)
        headers = {'X-bacnet-timeout':'3', 'Content-Type':'application/json'}
        res = requests.get(url, headers=headers, timeout=5)
        self.assertEqual(res.status_code, 202)
        self.assertTrue('value' in res.json().keys())
        return


    def test_ReadPropertyMultiple(self):

        url = 'http://{}:{}/readpropertymultiple/'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        bacnet_object1 = {'object':'analogValue:10000',
                          'property':'presentValue'}
        bacnet_object2 = {'object':'analogValue:10001',
                          'property':'presentValue'}
        bacnet_object3 = {'object':'analogValue:10002',
                          'property':'all'}
        body = {'bacnet_objects':[bacnet_object1, bacnet_object2, bacnet_object3],
                'address':'192.168.1.100'}

        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=2)

        self.assertEqual(res.status_code, 202)
        self.assertTrue("('analogValue', 10000)" in res.json().keys())
        self.assertTrue("('analogValue', 10001)" in res.json().keys())
        self.assertTrue("('analogValue', 10002)" in res.json().keys())

        return


    def test_invalid_bacnet_object(self):
        return

    def test_invalid_address(self):
        return

    def test_whois(self):
        return

    def test_invalid_whois(self):
        return

    def test_routed_MSTP_object(self):
        return

    def test_(self):
        return



if __name__ == '__main__':
    # Three ways to run test suites or their methods

    # # Method 1 - Running a test case
    # suite = unittest.TestLoader().loadTestsFromTestCase(BacnetHTTPServerTest)
    # unittest.TextTestRunner(verbosity=2).run(suite)

    # # Method 2 - Running a test case
    # unittest.main(BacnetHTTPServerTest())

    # Method 3 - Running a SINGLE test method from a test case
    suite = unittest.TestSuite()
    suite.addTest(BacnetHTTPServerTest('test_ReadPropertyMultiple'))
    runner = unittest.TextTestRunner()
    runner.run(suite)






#%%

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()
    return

def read_process():
    try:  line = process_queue.get_nowait() # or q.get(timeout=.1)
    except Empty:
        print('no output yet')
    else: # got line
        print(line)
    return

class OfflineBacnetTest(unittest.TestCase):

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

        # Create a BACnet Client to do testing
        self.init_bacnet_client()

        return None

    def tearDown(self):
        self.close_bacnet_client()
        return None

    def init_bacnet_client(self):
        """Initialize the BACnet client application that is used to communicate
        on the network"""

        global process, t
        executable = r'C:\Users\z003vrzk\.spyder-py3\Scripts\weather_station\httpServer.py'
        args = ['python', executable,
                '--ini', ini_file,
                '--host', HOST,
                '--port', PORT,
                '--debug', '__main__.ThreadedHTTPRequestHandler',
                '--debug','__main__',
                ]
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        # Give time for process to start up
        time.sleep(3)
        t = threading.Thread(target=enqueue_output, args=(process.stdout, process_queue))
        t.daemon = True # thread dies with the program
        t.start()
        print("Read thread is alive : ", t.is_alive())

        return


    def close_bacnet_client(self):
        """Call kill() method on process returned by subprocess.Popen"""
        if not process:
            print("Process has not been started")
            raise(Exception("Attempted process terminate without running process"))
        elif process.poll() == 1:
            # Process is already closed
            print("Process already terminated")
        else:
            process.kill()

        return


    def test_parse(self):
        path = 'http://localhost:8080/read/192.168.1.100/analogInput:0'
        parsed_params = urlparse(path)
        print('parsed parameters from URL', parsed_params)
        args = parsed_params.path.split("/")
        print('Parsed parameters from path', args)

        self.assertEqual(args[0], '')
        self.assertEqual(args[1], 'read')
        self.assertEqual(args[2], '192.168.1.100')
        self.assertEqual(args[3], 'analogInput:0')

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


    def test_make_iocb(self):
        """inputs
        -------
        read_args : (iterable) of ('', 'read', <address>, <object_identifier>)
            address : (str) BACnet IP address of device we are trying to
                communicate with. Example 192.168.1.100
            object_identifier : (str) BACnet Object Identifier of the device
                defined in 'address'. This is of the form
                <ObjectType>:<Instance>.
                Typical values for ObjectType can be found where?
            """

        read_args=('192.168.1.100', 'analogValue:1')

        addr, obj_id = read_args[:2]
        obj_id = ObjectIdentifier(obj_id).value

        # Enforce a specific object type
        if not get_object_class(obj_id[0]): # bacpypes.object.AnalogInputObject
            raise ValueError("unknown object type")

        # implement a default property, the bain of committee meetings
        if len(read_args) == 3:
            prop_id = read_args[2]
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
        if len(read_args) == 5:
            request.propertyArrayIndex = int(read_args[4])

        # make an IOCB
        iocb = IOCB(request)

        # Information related to destination and network control (context information and processing instructions)
        apci_contents = request.apci_contents()
        self.assertEqual(apci_contents['destination'], read_args[0])
        # Read property requests always require a confirmation PDU
        self.assertEqual(apci_contents['apduType'], 'ConfirmedRequestPDU')
        # This test only applies to ReadPropertyRequests
        self.assertEqual(apci_contents['apduService'], 'ReadPropertyRequest')

        # Information related to DATA
        apdu_contents = request.apdu_contents()
        self.assertEqual(apdu_contents['function'], 'ReadPropertyRequest')
        self.assertEqual(apdu_contents['objectIdentifier'], ('analogValue', 1))
        self.assertEqual(apdu_contents['propertyIdentifier'], 'presentValue')

        # Testing of IOCB - not much to test
        self.assertIsInstance(iocb.args[0], ReadPropertyRequest)
        return None


if __name__ == '__main__':
    # Three ways to run test suites or their methods

    # Method 1 - Running a test case
    suite = unittest.TestLoader().loadTestsFromTestCase(OfflineBacnetTest)
    unittest.TextTestRunner(verbosity=2).run(suite)