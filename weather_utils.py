# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 21:16:10 2020

@author: z003vrzk
"""
# Python imports
import re
import os
import subprocess
import sys

def check_network_interface(interface_name):
    """Check if a specific network interface is active
    Inputs
    -------
    interface_name : (str) Name of the network interface to test
    Outputs
    --------
    tuple (adapter_enabled, adapter_connected)
    adapter_enabled : (bool)
    adapter_connected : (bool)
    """

    if sys.platform == 'win32':
        adapter_enabled, adapter_connected = _check_network_interface_windows(interface_name)
    else:
        msg='Network interface check only defined for windows platform'
        raise NotImplementedError(msg)

    return adapter_enabled, adapter_connected

def _check_network_interface_windows(interface_name):

    cmd = ['netsh','interface','show','interface']
    process = subprocess.run(cmd, stdout=subprocess.PIPE)
    """
    'Admin State    State          Type             Interface Name',
     '-------------------------------------------------------------------------',
     'Enabled        Connected      Dedicated        Wi-Fi'
     """

    adapter_enabled = False
    adapter_connected = False
    for line in process.stdout.decode().split('\r\n'):
        if re.search('Ethernet', line):
            if re.search('Enabled', line):
                adapter_enabled = True
            if re.search('Connected', line):
                adapter_connected = True

    return adapter_enabled, adapter_connected