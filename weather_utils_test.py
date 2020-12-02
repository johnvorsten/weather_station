# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 20:00:35 2020

@author: z003vrzk
"""

# Python imports
import asyncio
from configparser import ConfigParser
from argparse import ArgumentParser
import json
from datetime import datetime
import logging

# Third party imports
import requests
from bacpypes.primitivedata import ObjectIdentifier

# Local imports
from CWOPpdu import CWOPPDU, Latitude, Longitude
from CWOPClient import cwop_client
from weather_utils import (check_network_interface, read_bacnet_server_ini,
                           test_bacnet_server, AsyncRecurringTimer,
                           BufferedSMTPHandler)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_log_file = 'CWOPWeatherPy.log'

# Create handlers for 1. Console 2. File 3. Email
ch = logging.StreamHandler() # Stream/console handler
ch.setLevel(logging.DEBUG) # >DEBUG goes to console
fh = logging.FileHandler(_log_file) # file handler
fh.setLevel(logging.INFO) # >INFO goes to file

chformat = logging.Formatter('%(name)s - %(levelname)s -%(message)s')
fhformat = logging.Formatter('%(asctime)s %(name)s - %(levelname)s -%(message)s')
ch.setFormatter(chformat)
fh.setFormatter(fhformat)
logger.addHandler(ch) # Console / Stream
logger.addHandler(fh) # File


#%%

async def main():
    print("Calling main()")
    logger.info("Calling main()")
    return


if __name__ == '__main__':
    call_period = 10 # Seconds

    logger.debug("Starting Main")

    # Begin the recurring task
    logger.info("Starting main loop. The loop will run " +
                "continuously every {} seconds.".format(call_period))
    recurring_timer = AsyncRecurringTimer(call_period, main, recurring=True)

    try:
        # There is an existing event loop
        # AKA working in ipython
        loop = asyncio.get_running_loop()
        client_coroutine = recurring_timer.start()
        client_task = asyncio.create_task(client_coroutine)

    except RuntimeError:
        # There is no running event loop
        logger.info("Starting new Async Event Loop")
        loop = asyncio.get_event_loop()
        # Now.. I need to set the coroutine to be executed in the loop
        # once started
        client_coroutine = recurring_timer.start()
        client_task = loop.create_task(client_coroutine)

    try:
        loop.run_forever()
    finally:
        recurring_timer.cancel()
        loop.close()


    """First try
    THERE ARE A NUMBER OF PROBLEMS HERE -
    1. asyncio.get_event_loop will check if there is no current event loop
    set in the current OS thread, the OS thread is main, and set_event_loop()
    has not yet been called, asyncio will create a new event loop and set it
    as the current one.

    2. Do not use asyncio.create_task when there is no running event loop. First
    I have to schedule a task to be run in an event loop through loop.create_task

    3. Other stuff..."""
    # if asyncio.get_event_loop() is None: # This doesnt work
    #     # There is no running event loop
    #     logger.info("Starting new Async Event Loop")
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     client_coroutine = recurring_timer.start()
    #     client_task = asyncio.create_task(client_coroutine)

    # else:
    #     # There is an existing event loop
    #     # AKA working in ipython
    #     logger.info("Executing in exesting event loop")
    #     loop = asyncio.get_event_loop()
    #     if loop.is_running():
    #         client_coroutine = recurring_timer.start()
    #         client_task = asyncio.create_task(client_coroutine)

    #     else:
    #         pass

    # try:
    #     loop = asyncio.get_event_loop()
    #     loop.run_forever()
    # finally:
    #     recurring_timer.cancel()
    #     loop.stop()

    """Second try - sleep while task is not complete
    THIS DOES NOT WORK - LEARN FROM MY MISTAKES"""
    # # Wait for initial task to complete
    # while not client_task.done():
    #     asyncio.sleep(1)

    # # The recurring_timer._task is not set until the second iteration
    # # Now we wait in an infinite loop for the client task to keep running
    # while recurring_timer.is_task_running():
    #     asyncio.sleep(5)


#%%

"""This method also works. First we define a callback (Not a coroutine) and
schedule the callback to be placed on the loop.
Then we start the loop
In this case IDK if the loop will exit - it will probably just run forever"""


def hello_world():
    """A callback to print 'Hello World' and stop the event loop"""
    print('Hello World')
    return

loop = asyncio.new_event_loop()

# Schedule a call to hello_world()
loop.call_soon(hello_world)

# Blocking call interrupted by loop.stop()
try:
    loop.run_forever()
finally:
    loop.close()


#%%

async def some_task(name, number):
    print('task ', name, ' started')
    await asyncio.sleep(number)
    print('task ', name, ' finished')


async def loop_executer(loop):
    # you could use even while True here
    while loop.is_running():
        tasks = [
            some_task("A", 2),
            some_task("B", 5),
            some_task("C", 4)
        ]
        await asyncio.wait(tasks)

ev_loop = asyncio.get_event_loop()
task = ev_loop.create_task(loop_executer(ev_loop))
ev_loop.run_forever()