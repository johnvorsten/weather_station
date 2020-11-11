# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 20:17:36 2020

@author: z003vrzk
"""

# Python imports
import asyncio
import argparse
import datetime

# Third party imports

# Local imports
from coordinate import Latitude, Longitude
from CWOPpdu import CWOPPDU
from CWOPClient import tcp_echo_client

# Declarations
SERVER_HOST = 'cwop.aprs.net' # For CWxxxx DWxxxx EWxxxx or FWxxxx provider_id
SERVER_PORT = 14580 # Official
_debug = False

# Arguments
parser = argparse.ArgumentParser(description='CWOP Client')
parser.add_argument('provider_id', metavar='provider_id', type=str, help='Provider ID of weather Station')
parser.add_argument('latitude', metavar='lat', type=float, help='Latitude of measurement')
parser.add_argument('longitude', metavar='long', type=float, help='Longitude of measurement')
parser.add_argument('debug', metavar='debug', type=bool, help='Debug Command')
args = parser.parse_args()
_debug = args.debug
long = Longitude(args.long)
lat = Latitude(args.lat)
base_kwargs = {'time':datetime.now(),
       'longitude':long,
       'latitude':lat,
       }
pdu = CWOPPDU(args.provider_id, **base_kwargs)


#%%


async def main(pdu):
    await tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT)
    return


if __name__ == '__main__':

    if asyncio.get_event_loop() is None:
        # There is no running event loop
        asyncio.run(main(pdu))

    else:
        # There is an existing event loop
        # AKA working in ipython
        loop = asyncio.get_event_loop()
        if loop.is_running():
            client_coroutine = tcp_echo_client(pdu, SERVER_HOST, SERVER_PORT)
            client_task = asyncio.create_task(client_coroutine)

        else:
            pass