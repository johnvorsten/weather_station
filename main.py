# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 21:07:15 2020

@author: z003vrzk
"""

# Python imports
import subprocess
from queue import Queue, Empty
import time
import threading
from configparser import ConfigParser

# Third party imports
import requests

# Local imports
from CWOPpdu import CWOPPDU
from CWOPClient import cwop_client
from BACnetHTTPServer import HTTPRequestHandler, ThreadedTCPServer
from weather_utils import check_network_interface

#### Declarations ####
config = ConfigParser()
config_file = './weather_config.ini'
config.read(config_file)
sections = config.sections()
assert 'bacnet_client' in sections, '{} ini section is required'.format('bacnet_client')
assert 'bacnet_server' in sections, '{} ini section is required'.format('bacnet_server')
assert 'http_server' in sections, '{} ini section is required'.format('http_server')

# BACnet HTTP Server and client declarations
process_queue = Queue()
BAC_ini_file = './bacnet_client.ini'
BACHTTPServerHost = config['http_server']['BACHTTPServerHost']
BACHTTPPort = config['http_server']['BACHTTPPort']
BAC_Router_Address = '192.168.1.100' # BACnet router address

# Weather CWOP Client & Server declarations
CWOP_SERVER_HOST = 'cwop.aprs.net'
CWOP_SERVER_PORT = 14580

# Check if network interface is active
INTERFACE_NAME = 'Ethernet'
adapter_enabled, adapter_connected = check_network_interface(INTERFACE_NAME)
if not adapter_enabled or not adapter_connected:
    msg='The specified network interface adapter is not connected'
    raise OSError(msg)


"""
X. Read configuration file for HTTP, BACnet client, BACnet Server
1. Start the BACnet HTTP Server in a separate process
2. Test the BACnet HTTP Server to see if it is up and connected
X. Test the BACnet Client/server to see if it is running
X. Test BACnet router to see if it is running
X. Test BACnet weather client to see if it is connected
X. Use a Try/Except to see if the internet connection was successful
X. Send data to FindU Server
"""


#%%


def read_bacnet_client_ini(config):
    """
    bacnet_object1 = {'object':'analogValue:10000',
                      'property':'presentValue'}
    bacnet_object2 = {'object':'analogValue:10001',
                      'property':'presentValue'}
    bacnet_object3 = {'object':'analogValue:10002',
                      'property':'all'}
    body = {'bacnet_objects':[bacnet_object1, bacnet_object2, bacnet_object3],
            'address':'192.168.1.100'}
    """
    body = {'bacnet_objects':[],
            'address':None}
    read_objects = config['bacnet_server']['read_objects'].split(',')
    read_properties = config['bacnet_server']['read_objects'].split(',')

    if len(read_objects) <= 0:
        msg=('The configuration file for the BACnet client must have at ' +
        'least one read_objects specification')
        raise ValueError(msg)

    if len(read_properties) <= 0:
        msg=('The configuration file for the BACnet client must have at ' +
        'least one read_properties specification')
        raise ValueError(msg)

    if len(read_properties) != len(read_objects):
        msg=('The configuration file for the BACnet client must have the ' +
        'same number of bac_objects speficiations as bac_properties. ' +
        'Got {} bac_objects and {} bac_properties'\
            .format(len(read_objects), len(read_properties)))
        raise ValueError(msg)

    for bac_object, bac_property in zip(read_objects, read_properties):
        read_object = {'object':bac_object,
                       'property':bac_property}
        body['bacnet_objects'].append(read_object)

    body['address'] = config['bacnet_server']['address']

    return body


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


def start_BACnet_HTTP_Server(BACHTTPServerHost, BACHTTPPort, BAC_ini_file):
    """Start the BACnet HTTP server & client in a separate process"""

    """Initialize the BACnet client application that is used to communicate
    on the network"""

    global process, enqueue_thread
    executable = r'./BACnetHTTPServer.py'
    args = ['python', executable,
            '--ini', BAC_ini_file,
            '--host', BACHTTPServerHost,
            '--port', BACHTTPPort,
            '--debug', '__main__.ThreadedHTTPRequestHandler',
            ]
    process = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    # Give time for process to start up
    time.sleep(3)
    enqueue_thread = threading.Thread(target=enqueue_output, args=(process.stdout, process_queue))
    enqueue_thread.daemon = True # thread dies with the program
    enqueue_thread.start()
    print("Read thread is alive : ", enqueue_thread.is_alive())

    return


def close_BACnet_HTTP_Server():
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


def test_bacnet_server(BACHTTPServerHost, BACHTTPPort):
    """Send a request to the BACnet HTTP server to see if it is active"""
    # Make a simple request
    url = 'http://{}:{}'.format(BACHTTPServerHost, BACHTTPPort)
    headers = {'X-bacnet-timeout':'3', 'Content-Type':'application/json'}
    res = requests.head(url, headers=headers, timeout=5)
    if res.status_code == 200:
        return True
    else:
        return False


def test_bacnet_weather_connected(BACHTTPServerHost, BACHTTPPort, BACServerAddress):
    """Send a BACnet request to the specified BACnet server (actual sensor)
    to see if it is active"""

    # This is not implemented yet :(
    # Make some requests
    url = 'http://{}:{}/whois/{}'.format(BACHTTPServerHost,BACHTTPPort, BACServerAddress)
    headers = {'X-bacnet-timeout':'3', 'Content-Type':'application/json'}
    res = requests.get(url, headers=headers, timeout=5)

    return res.status_code






def main():
    """
    X. Read configuration file for HTTP, BACnet client, BACnet Server

    2. Test the BACnet HTTP Server to see if it is up and connected
    X. Test the BACnet Client/server to see if it is running
    X. Test BACnet router to see if it is running
    X. Test BACnet weather client to see if it is connected
    X. Use a Try/Except to see if the internet connection was successful
    X. Send data to FindU Server
    """

    # X. Read configuration file for HTTP, BACnet client, BACnet Server
    body = read_bacnet_client_ini(config)

    # 2. Test the BACnet HTTP Server to see if it is up and connected
    res = test_bacnet_server(BACHTTPServerHost, BACHTTPPort)
    if res:
        pass
    else:
        msg=('The BACnet HTTP Server is not responding. Exiting main '+
        'HTTP Server configuration {},{},{}'.format(BACHTTPServerHost, BACHTTPPort))
        raise RuntimeError(msg)

    # X. Test the BACnet Client/server to see if it is running

    return None

