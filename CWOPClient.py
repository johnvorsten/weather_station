# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 13:39:53 2020

@author: z003vrzk
"""

# Python imports
import asyncio

# Third party imports

# Local imports
from coordinate import Latitude, Longitude
from CWOPpdu import CWOPPDU

# Declarations
SERVER_HOST = 'cwop.aprs.net'
SERVER_PORT = 14580
_debug = True
pdu = False # No default for sending message


async def tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT):
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
    soo1 = await reader.read(-1)
    if _debug:
        print('Client Received {}\n'.format(soo1))

    # 2. Send login line
    if _debug:
        print('Client sending login line {}\n'.format(pdu.login_line))
    writer.write(pdu.login_line) # Bytes
    writer.write(b'\r\n')
    await writer.drain()

    # 3. Receive acknowledgement
    soo3 = await reader.read(-1)
    if _debug:
        print('Client Received Acknowledgement {}\n'.format(soo3))

    # 4. Send APRS packet
    if _debug:
        print('Client Sending data {}\n'.format(pdu.pdu_data_packet))
    writer.write(pdu.pdu_data_packet)
    writer.write(b'\r\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()

    return


async def main(pdu):
    await tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT)
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
            client_coroutine = tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT)
            client_task = asyncio.create_task(client_coroutine)

        else:
            pass

    else:
        raise ValueError('Dont execute this script. You need to define a PDU')
