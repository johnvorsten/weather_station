# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 21:07:15 2020

TODO add logging
TODO add supervisor

@author: z003vrzk
"""

# Python imports
import asyncio
from configparser import ConfigParser
import json
from datetime import datetime
import logging

# Third party imports
import requests
from bacpypes.primitivedata import ObjectIdentifier

# Local imports
from CWOPpdu import CWOPPDU, Latitude, Longitude
from CWOPClient import cwop_client
from weather_utils import (check_network_interface, read_bacnet_client_ini,
                           enqueue_output, read_process,
                           start_BACnet_HTTP_Server, close_BACnet_HTTP_Server,
                           test_bacnet_server, AsyncRecurringTimer,
                           BufferedSMTPHandler)

#### Declarations ####
config = ConfigParser()
config_file = './weather_config.ini'
config.read(config_file)
sections = config.sections()
assert 'bacnet_client' in sections, 'bacnet_client ini section is required'
assert 'bacnet_server' in sections, 'bacnet_server ini section is required'
assert 'http_server' in sections, 'http_server ini section is required'
assert 'cwop_client' in sections, 'cwop_client ini section is required'
# BACnet HTTP Server and client declarations
BAC_ini_file = './bacnet_client.ini'
BACHTTPServerHost = config['http_server']['BACHTTPServerHost']
BACHTTPPort = config['http_server']['BACHTTPPort']

# Weather CWOP Client & Server declarations
CWOP_SERVER_HOST = 'cwop.aprs.net'
CWOP_SERVER_PORT = 14580
provider_id = config['cwop_client']['provider_id']
latitude = float(config['cwop_client']['latitude'])
longitude = float(config['cwop_client']['longitude'])
call_period = int(config['cwop_client'].get('call_period', 5*60))

# Check if network interface is active
INTERFACE_NAME = 'Ethernet'
adapter_enabled, adapter_connected = check_network_interface(INTERFACE_NAME)
if not adapter_enabled or not adapter_connected:
    msg='The specified network interface adapter is not connected'
    raise OSError(msg)

# Logging
_log_file = 'CWOPWeatherPy.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers for 1. Console 2. File 3. Email
ch = logging.StreamHandler() # Stream/console handler
ch.setLevel(logging.DEBUG) # >DEBUG goes to console
fh = logging.FileHandler(_log_file) # file handler
fh.setLevel(logging.INFO) # >INFO goes to file

if config['error_reporting']['mailhost']:
    mailhost=(str(config['error_reporting']['mailhost']),
              int(config['error_reporting']['mailport']))
    fromaddr=config['error_reporting']['fromaddr']
    toaddrs=config['error_reporting']['toaddrs'].split(',')
    credentials=tuple(config['error_reporting']['credentials'].split(','))
    eh = BufferedSMTPHandler( # Email handler
        capacity=20,
        mailhost=mailhost,
        fromaddr=fromaddr,
        toaddrs=toaddrs,
        subject='CWOP Client Error',
        credentials=credentials,
        secure=(),
        )
    ehformat = logging.Formatter(
    ("Message type:     %(name)s %(levelname)s" + "\n" +
    "Time:             %(asctime)s" + "\n" +
    "Message:          %(message)s")
    )
    eh.setFormatter(ehformat)
    eh.setLevel(logging.ERROR) # >ERROR goes to email
    logger.addHandler(eh) # Email

chformat = logging.Formatter('%(name)s - %(levelname)s -%(message)s')
fhformat = logging.Formatter('%(asctime)s %(name)s - %(levelname)s -%(message)s')
ch.setFormatter(chformat)
fh.setFormatter(fhformat)
logger.addHandler(ch) # Console / Stream
logger.addHandler(fh) # File

"""
X. Read configuration file for HTTP, BACnet client, BACnet Server
X. Test the BACnet HTTP Server to see if it is up and connected
X. Test the BACnet Client/server to see if it is running
X. Test BACnet router to see if it is running
X. Test BACnet weather client to see if it is connected
X. Use a Try/Except to see if the internet connection was successful
X. Send data to FindU Server
"""

#%%


async def main():
    """
    X. Request data from BACnet server
    X. Error check HTTP Client/Server API response
    X. Form CWOP Protocol data unit
    X. Send data to FindU Server
    """

    # X. Read weather information from BACnet server through the HTTP
    # API
    url = 'http://{}:{}/readpropertymultiple/'.format(BACHTTPServerHost, BACHTTPPort)
    headers = {'Content-Type':'application/json', 'X-bacnet-timeout':'3'}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=2)
    except Exception as e:
        msg='HTTP POST unsuccessful\n' + str(res.status_code) + str(res.request)
        logger.error(str(e) + '\n' + msg)

    if res.headers['Content-Type'] != 'application/json':
        # An error was reported by the BACnet/HTTP server
        # Errors are reported with Content-Type = text/plain
        msg=('Error at BACnet HTTP Server. Content dump: {}'.format(res.content))
        logger.error(msg)

    if res.status_code != 202:
        msg=('Error at BACnet HTTP Server. Content dump: {}'.format(res.content))
        logger.warning(msg)

    try:
        # Parse the resposne (Should be JSON)
        res_json = res.json()
        for bac_obj in body['bacnet_objects']:
            # Make sure the response includes all the requested bacnet objects
            identifier = ObjectIdentifier(bac_obj['object']).value
            if not str(identifier) in res_json.keys():
                msg=('The BACnet HTTP client did not respond correctly to '+
                     'the request.\nRequest : {}\nResponse : {}\n'\
                         .format(res.request, res.content))
                # TODO Log error
                raise RuntimeError(msg)
    except json.JSONDecodeError as e:
        # Log the error
        msg=('The BACnet HTTP client did not respond correctly to '+
             'the request.\nRequest : {}\nResponse : {}\n'\
                 .format(res.request, res.content))
        logger.error(e)

    # X. Send data to FindU Server
    try:
        pdu_kwargs = {'time':datetime.now().strftime('%d%H%M'),
                      'latitude':Latitude(latitude),
                      'longitude':Longitude(longitude),
                      'temperature':res_json["('analogInput', 1)"]['presentValue'],
                      'humidity':res_json["('analogInput', 4)"]['presentValue'],
                      'dewpoint':res_json["('analogInput', 8)"]['presentValue'],
                      'co2':res_json["('analogInput', 12)"]['presentValue'],
                      }
        pdu = CWOPPDU(**pdu_kwargs)
        await cwop_client(pdu, CWOP_SERVER_HOST, CWOP_SERVER_PORT)
    except Exception as e:
        logger.exception(str(e))

    return None



if __name__ == '__main__':
    global body
    # X. Read configuration file for HTTP, BACnet client, BACnet Server
    # Read the ini file and create the POST request body
    """Example Body
    {'bacnet_objects': [{'object': 'analogInput:1', 'property': 'presentValue'},
      {'object': 'analogInput:4', 'property': 'presentValue'},
      {'object': 'analogInput:8', 'property': 'presentValue'},
      {'object': 'analogInput:12', 'property': 'presentValue'}],
     'address': '665002'}
    """
    logger.debug("Starting Main")
    logger.debug("Reading ini configuration file")
    body = read_bacnet_client_ini(config)
    logger.debug("Configuration Options : {}".format(body))

    # X. Test the BACnet HTTP Server to see if it is up and connected
    try:
        res = test_bacnet_server(BACHTTPServerHost, BACHTTPPort)
        if res: # Boolean
            logger.info("BACnet HTTP Server is responding")
        else:
            msg="BACnet HTTP Server did not respond to health check"
            logger.warning(msg)
            raise requests.ConnectionError(msg)
    except Exception as e:
        msg=('The BACnet HTTP Server is not responding. Exiting main. '+
        'HTTP Server configuration {},{}'.format(BACHTTPServerHost, BACHTTPPort))
        logger.warning(e)
        raise e

    # X. Begin the recurring task
    logger.info("Starting main loop. The CWOP Client loop will run " +
                "continuously every {} seconds.".format(call_period))
    recurring_timer = AsyncRecurringTimer(call_period, main, recurring=True)
    if asyncio.get_event_loop() is None:
        # There is no running event loop
        logger.info("Starting new Async Event Loop")
        asyncio.run(recurring_timer.start())

    else:
        # There is an existing event loop
        # AKA working in ipython
        logger.info("Executing in exesting event loop")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            client_coroutine = recurring_timer.start()
            client_task = asyncio.create_task(client_coroutine)

        else:
            pass