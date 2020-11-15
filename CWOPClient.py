# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 13:39:53 2020

@author: z003vrzk
"""

# Python imports
import asyncio
import socket

# Third party imports

# Local imports
from coordinate import Latitude, Longitude
from CWOPpdu import CWOPPDU

# Declarations
SERVER_HOST = 'cwop.aprs.net'
SERVER_PORT = 14580
_debug = False
pdu = False # No default for sending message

#%%

async def cwop_client(pdu, SERVER_HOST, SERVER_PORT):
    """
    Parameters
    ----------
    pdu : (CWOPpdu.CWOPPDU)
        DESCRIPTION.
    SERVER_HOST : TYPE
        DESCRIPTION.
    SERVER_PORT : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    Each TCP connection will use port 14580
    1.
    The ARPS server sends a text line indicating the server software we
    connected to. Receive one text line terminated with cr/lf. This line
    identifies server software.
    2.
    Upon receiving that line, your client will send a login line.
    3.
    Once that is entered (terminate with cr/lf), you will receive an
    acknowledgement line from the server and it can be safely ignored
    4.
    After receiving the login acknowledgement, the server is ready to take the
    single APRS "packet" with the weather data. After the packet is sent, your
    client can safely disconnect from the server. There will be no
    acknowledgement of the packet being received at the server (the
    acknowledgement is handled by the TCP underlying protocol). The APRS
    "packet" is also terminated by cr/lf.
    """
    if _debug:
        print('Client connecting to server\n')
    reader, writer = await asyncio.open_connection(
        SERVER_HOST, SERVER_PORT)

    # 1. Receive connection line
    """
    # This actually isnt needed, even thought the CWOP spec acts like it is...
    soo1 = await reader.read(-1)
    if _debug:
        print('Client Received {}\n'.format(soo1))
    """

    # 2. Send login line
    if _debug:
        print('Client sending login line {}\n'.format(pdu.login_line))
    writer.write(pdu.login_line + b'\n') # Bytes
    await writer.drain()

    # 3. Receive acknowledgement
    """
    # This is also not needed (and actually breaks the program)
    soo3 = await reader.read(-1)
    if _debug:
        print('Client Received Acknowledgement {}\n'.format(soo3))
    """

    # 4. Send APRS packet
    if _debug:
        print('Client Sending data {}\n'.format(pdu.pdu_data_packet))
    writer.write(pdu.pdu_data_packet + b'\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    return


def _standard_socket():
    """Dont use this method, even though it works to send data through a
    standard socket"""

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


async def main(pdu):
    await cwop_client(pdu, SERVER_HOST, SERVER_PORT)
    return


if __name__ == '__main__':

    if asyncio.get_event_loop() is None and isinstance(pdu, CWOPPDU):
        # There is no running event loop
        asyncio.run(main(pdu))

    elif isinstance(pdu, CWOPPDU):
        # There is an existing event loop
        # AKA working in ipython
        loop = asyncio.get_event_loop()
        if loop.is_running():
            client_coroutine = cwop_client(pdu, SERVER_HOST, SERVER_PORT)
            client_task = asyncio.create_task(client_coroutine)

        else:
            pass

    else:
        raise ValueError('Dont execute this script. You need to define a PDU')
