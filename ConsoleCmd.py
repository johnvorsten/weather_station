# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 21:53:59 2020

@author: z003vrzk
"""

# Third party imports
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping

# from bacpypes.app import BIPSimpleApplication
# from bacpypes.local.device import LocalDeviceObject

_debug = 0
_log = ModuleLogger(globals())

#%%

"""A simple console commnad for running my future program from
the command line

How to use this module
(cmd) C:\>python ConsoleCmd.py
> help

Documented commands (type help <topic>):
========================================
EOF  buggers  bugin  bugout  exit  gc  help  shell  something

> help something
something <arg> - do something
> something --my-argument arg1
do something --my-argument arg1

"""

@bacpypes_debugging
class SampleConsoleCmd(ConsoleCmd):

    cache = {}

    def do_something(self, arg):
        """something <arg> - do something"""
        print('do something', arg)
        return None

    def do_set(self, arg):
        if _debug: SampleConsoleCmd._debug("do_set: %r", arg)
        try:
            key, value = arg.split()
            self.cache[key] = value
        except ValueError:
            print(e)
        return None

    def do_del(self, arg):
        """del <key> - delete a cache entry"""
        if _debug: SampleConsoleCmd._debug("do_del: %r", arg)
        try:
            del self.cache[arg]
        except:
            print(arg, "Not in cache")
        return None

    def do_dump(self, arg):
        """dump - nicely print the cache"""
        if _debug: SampleConsoleCmd._debug("do_dump: %r", arg)
        print(self.cache)
        return None

def main():
    # parse the command line arguments
    # args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("   - args: %r", args)

    # Make a device object - Not required for this simple console cmd
    # this_device = LocalDeviceObject

    # Initialize application - Not required for this simple console cmd
    # this_application = SampleApplication(this_device, args.ini.address)

    # Make Console
    this_console = SampleConsoleCmd()
    if _debug: _log.debug("   - this_console: %r", this_console)

    # Sleeping with threads
    enable_sleeping()

    _log.debug("Running")
    run()
    _log.debug("Finish")

    return None

if __name__ == '__main__':
    main()
