# -*- coding: utf-8 -*-
"""
Created on Sun Nov  8 20:07:15 2020

@author: z003vrzk
"""

# Python imports
import asyncio
import unittest
from datetime import datetime
import socket

# Third party imports

# Local imports
from coordinate import Latitude, Longitude
from CWOPpdu import CWOPPDU
from CWOPClient import tcp_echo_client

# Declarations
SERVER_HOST = 'cwop.aprs.net'
SERVER_PORT = 14580


#%%

def manual_test():

    _debug = True
    data_packet = b'FW8400>APRS,TCPIP*:@110649z2945.13N/09532.50W_.../...g...t...r...p...P...b...h...'
    login_line = b'user FW8400 pass -1 vers PythonCWOP 1.0'
    SERVER_HOST = 'cwop.aprs.net'
    SERVER_PORT = 14580

    if _debug:
        print('Client connecting to server\n')
    reader, writer = await asyncio.open_connection(
        host=SERVER_HOST,
        port=SERVER_PORT,
        family=socket.AF_INET, # Address and protocol family
        sock=socket.SOCK_STREAM, # Socket type
        )

    # 1. Receive connection line
    soo1 = await reader.read(-1)
    if _debug:
        print('Client Received {}\n'.format(soo1))

    # 2. Send login line
    if _debug:
        print('Client sending login line {}\n'.format(login_line))
    writer.write(pdu.login_line + b'\n') # Bytes
    await writer.drain()

    # 3. Receive acknowledgement
    soo3 = await reader.read(-1)
    if _debug:
        print('Client Received Acknowledgement {}\n'.format(soo3))

    # 4. Send APRS packet
    if _debug:
        print('Client Sending data {}\n'.format(data_packet))
    writer.write(data_packet + b'\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    return

def manual_test_2():
    _debug = True
    data_packet = b'FW8400>APRS,TCPIP*:@110649z2945.13N/09532.50W_.../...g...t...r...p...P...b...h...'
    login_line = b'user FW8400 pass -1 vers PythonCWOP 1.0'
    SERVER_HOST = 'cwop.aprs.net'
    SERVER_PORT = 14580

    if _debug:
        print('Client connecting to server\n')
    # The socket type will automatically be socket.SOCK_STREAM
    reader, writer = await asyncio.open_connection(
        host=SERVER_HOST,
        port=SERVER_PORT,
        family=socket.AF_INET, # Address and protocol family
        )

    # Send login line
    writer.write(login_line + b'\n')
    await writer.drain()

    # Send data
    writer.write(data_packet + b'\n')
    await writer.drain()

    # Close connection
    writer.close()
    await writer.wait_closed()

    return


def standard_socket():

    SERVER_HOST = 'cwop.aprs.net'
    SERVER_PORT = 14580
    data_packet = b'FW8400>APRS,TCPIP*:@110649z2945.13N/09532.50W_.../...g...t...r...p...P...b...h...'
    login_line = b'user FW8400 pass -1 vers PythonCWOP 1.0'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))
    # Login
    s.send(login_line + b'\n')
    s.send(data_packet + b'\n')
    s.shutdown(0)
    s.close()

    return




class CWOPClientTest(unittest.TestCase):

    def setUp(self):
        global lat, long, provider_id, base_kwargs, pdu
        # Form a fake PDU for testing CWOP Client
        long = Longitude(-95.458310)
        lat = Latitude(29.752320)
        base_kwargs = {'time':datetime.now(),
               'longitude':long,
               'latitude':lat,
               }
        provider_id = 'FW8400'
        pdu = CWOPPDU(provider_id, **base_kwargs)

        return

    def test_client(self):

        if asyncio.get_event_loop() is None:
            # There is no running event loop
            asyncio.run(tcp_echo_client(pdu))

        else:
            # There is an existing event loop
            # AKA working in ipython
            loop = asyncio.get_event_loop()
            if loop.is_running():
                client_coroutine = tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT)
                client_task = asyncio.create_task(client_coroutine)

            else:
                pass

        return



if __name__ == '__main__':
    unittest.main(CWOPClientTest())