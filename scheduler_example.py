# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 07:17:31 2020

@author: z003vrzk
"""

import sched, time
s = sched.scheduler(time.time, time.sleep)
def print_time(a='default'):
    print("From print_time", time.time(), a)

def print_some_times():
    print(time.time())
    s.enter(10, 1, print_time)
    s.enter(5, 2, print_time, argument=('positional',))
    s.enter(5, 1, print_time, kwargs={'a': 'keyword'})
    s.run()
    print(time.time())

def periodic_print_some_times():
    s.enter(interval, action, actionargs=(), keywordargs)

print_some_times()

# How does this work with blocking?
s.enter(5, 1, print_time, kwargs={'a':'Threading?'})
s.run()
print(time.time())


#%%
"""Based off of
https://stackoverflow.com/a/18906292
"""

from threading import Timer, Lock, activeCount
from threading import enumerate as thread_enumerate
import time

class Periodic(object):
    """
    A periodic task running in threading.Timers
    """

    def __init__(self, interval, function, *args, **kwargs):
        self._lock = Lock()
        self._timer = None
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self._stopped = True
        if kwargs.pop('autostart', True):
            self.start()

    def start(self, from_run=False):
        self._lock.acquire()
        if from_run or self._stopped:
            self._stopped = False
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self._lock.release()

    def _run(self):
        self.start(from_run=True)
        self.function(*self.args, **self.kwargs)

    def stop(self):
        self._lock.acquire()
        self._stopped = True
        self._timer.cancel()
        self._lock.release()



def function(arg1, keyword='default'):
    print("Called from function", arg1, keyword)
    return None

print("starting")
periodic = Periodic(2, function, ('argument'), keyword='custom')

try:
    print("Number of active threads:", activeCount())
    for _thread in thread_enumerate():
        print(_thread.__str__())
    time.sleep(15) # Something I'm doing here... long running

finally:
    print("Number of active threads:", activeCount())
    periodic.stop()