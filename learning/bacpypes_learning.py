# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 06:48:00 2020

@author: z003vrzk
"""

# Python imports
import configparser
from datetime import datetime

# Third party imports
from bacpypes.comm import Client, Server, bind
from bacpypes.comm import Debug

# Local imports

# Keys
config_path = r"C:\Users\z003vrzk\.spyder-py3\Scripts\weather_station\config.ini"
config = configparser.ConfigParser()
config.read(config_path)
sections = config.sections()
assert 'bacnet_client' in sections
objectName = config['bacnet_client']['objectName']
address = config['bacnet_client']['address']
objectIdentifier = config['bacnet_client']['objectIdentifier']
maxApduLengthAccepted = config['bacnet_client']['maxApduLengthAccepted']
segmentationSupported = config['bacnet_client']['segmentationSupported']
maxSegmentsAccepted = config['bacnet_client']['maxSegmentsAccepted']
vendorIdentifier = config['bacnet_client']['vendorIdentifier']
foreignPort = config['bacnet_client']['foreignPort']
foreignBBMD = config['bacnet_client']['foreignBBMD']
foreignTTL = config['bacnet_client']['foreignTTL']

#%%

class WeatherClient(Client):

    def confirmation(self, pdu):
        print('Confirmation from client Protocol Data Unit : {}'.format(pdu))
        return None

class TestServer(Server):

    def indication(self, arg):
        """What is this doing?"""
        print('Working on : {}'.format(arg))
        self.response(arg.upper())
        return None



if __name__ == '__main__':
    client = WeatherClient()
    server = TestServer()
    bind(client, server)
    client.request('hi')

    # Add debugging into the middle of the stack
    # Upstream when traveling from server to client
    # Downstream when traveling from client to server
    d = Debug("middle")
    bind(client, d, server)
    client.request('Hi')

#%% Protocol data units

from bacpypes.comm import PDU

pdu = PDU(b'hello') # Data portion of PDU only
pdu.debug_contents()
# Add source and destination information
pdu = PDU(b'hello', source=1, destination=2)
pdu.pduSource = 1
pdu.pduDestination = 2
pdu.debug_contents()

# Encoding and decoding a PDU
"""THis process consists of consuming content from a PDU (data, source, destination)
and generating content in the destination
Think if Decoding a PDU like taking characters out of an array
Encoding a PDU is like stacking characters into an array"""
pdu = PDU(b'hello!!!', source=1, destination=2)
pdu.debug_contents()
pdu.get() # 104
pdu.get_short() # 25964
pdu.get_long() # 1819222305

pdu.put_long(1819222305)
pdu.put_short(25964)
pdu.put(104)
pdu.debug_contents()
print(str(pdu.pduData.decode('utf-8')))

#%% Addresses

# Local stations hold address data
from bacpypes.pdu import LocalStation, LocalBroadcast
from bacpypes.pdu import RemoteStation, RemoteBroadcast, GlobalBroadcast
addr1 = LocalStation(b'123456') # 6 octet long address
addr2 = LocalStation(12)
addr1.addrAddr
addr2.addrAddr
# When the byte string is six octets long followed by \xba \xc0 the
# Address is interpreted as an IP address
addr3 = LocalStation(b'\x01\x02\x03\x04\xba\xc0')
addr3.__repr__()
# the last octet is the port address
addr4 = LocalStation(b'1234\xba\xc1')
addr4.__repr__()

# Local broadcast - sent to all devices on the network
print(LocalBroadcast())
# Remote station - Destination other than local network
print(RemoteStation(15, 75)) # Network number,  integer
# Remote broadcast
print(RemoteBroadcast(15)) # Network number
# Global broadcast
print(GlobalBroadcast())