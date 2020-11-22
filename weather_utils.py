# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 21:16:10 2020

@author: z003vrzk
"""
# Python imports
import re
import subprocess
import sys
import asyncio
import time
import threading
from queue import Queue, Empty
from logging.handlers import BufferingHandler

# Third party imports
import requests

# Local imports

# Declarations
process_queue = Queue()


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


def read_bacnet_server_ini(config):
    """
    bacnet_object1 = {'object':'analogValue:10000',
                      'property':'presentValue'}
    bacnet_object2 = {'object':'analogValue:10001',
                      'property':'presentValue'}
    bacnet_object3 = {'object':'analogValue:10002',
                      'property':'all'}
    body = {'bacnet_objects':[bacnet_object1, bacnet_object2, bacnet_object3],
            'address':'192.168.1.100'}
    """
    body = {'bacnet_objects':[],
            'address':None}
    read_objects = config['bacnet_server']['read_objects'].split(',')
    read_properties = config['bacnet_server']['read_properties'].split(',')

    if len(read_objects) <= 0:
        msg=('The configuration file for the BACnet client must have at ' +
        'least one read_objects specification')
        raise ValueError(msg)

    if len(read_properties) <= 0:
        msg=('The configuration file for the BACnet client must have at ' +
        'least one read_properties specification')
        raise ValueError(msg)

    if len(read_properties) != len(read_objects):
        msg=('The configuration file for the BACnet client must have the ' +
        'same number of bac_objects speficiations as bac_properties. ' +
        'Got {} bac_objects and {} bac_properties'\
            .format(len(read_objects), len(read_properties)))
        raise ValueError(msg)

    for bac_object, bac_property in zip(read_objects, read_properties):
        read_object = {'object':bac_object,
                       'property':bac_property}
        body['bacnet_objects'].append(read_object)

    body['address'] = config['bacnet_server']['address']

    return body


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()
    return


def read_process():
    try:  line = process_queue.get_nowait() # or q.get(timeout=.1)
    except Empty:
        print('no output yet')
    else: # got line
        print(line)
    return


def start_BACnet_HTTP_Server(BACHTTPServerHost, BACHTTPPort, BAC_ini_file):
    """Start the BACnet HTTP server & client in a separate process"""

    """Initialize the BACnet client application that is used to communicate
    on the network"""

    global process, enqueue_thread
    executable = r'./BACnetHTTPServer.py'
    args = ['python', executable,
            '--ini', BAC_ini_file,
            '--host', BACHTTPServerHost,
            '--port', BACHTTPPort,
            '--debug', '__main__.HTTPRequestHandler',
            ]
    process = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    # Give time for process to start up
    time.sleep(3)
    enqueue_thread = threading.Thread(target=enqueue_output, args=(process.stdout, process_queue))
    enqueue_thread.daemon = True # thread dies with the program
    enqueue_thread.start()
    print("Read thread is alive : ", enqueue_thread.is_alive())

    return


def close_BACnet_HTTP_Server():
    """Call kill() method on process returned by subprocess.Popen"""

    if not process:
        print("Process has not been started")
        raise(Exception("Attempted process terminate without running process"))
    elif process.poll() == 1:
        # Process is already closed
        print("Process already terminated")
    else:
        process.kill()

    return


def test_bacnet_server(BACHTTPServerHost, BACHTTPPort):
    """Send a request to the BACnet HTTP server to see if it is active"""
    # Make a simple request
    url = 'http://{}:{}'.format(BACHTTPServerHost, BACHTTPPort)
    headers = {'X-bacnet-timeout':'3', 'Content-Type':'application/json'}
    res = requests.head(url, headers=headers, timeout=5)
    if res.status_code == 200:
        return True
    else:
        return False


class AsyncRecurringTimer:

    def __init__(self, call_period, callback, recurring=False):
        """
        Inputs
        -------
        call_period
        callback : (asyncio.)
        recurring : (bool)
        """
        self._call_period = call_period
        self._callback = callback
        self._recurring = recurring

        return

    async def _cycle(self, *args, **kwargs):
        # Calculate the time at the begining of the cycle
        self._cycle_start_time = time.time()

        # Execute the callback
        await self._callback(*args, **kwargs)

        # Calculate how long to sleep after the callback is executed
        timeout = self._timeout()
        await asyncio.sleep(timeout)

        # Schedle the callback to run again
        if self._recurring:
            self._task = asyncio.ensure_future(self._cycle(*args, **kwargs))

        return

    def _timeout(self):
        self._next_call = self._cycle_start_time + self._call_period
        return max(self._next_call - time.time(), 0)

    def cancel(self):
        self._task.cancel()
        return

    def start(self, *args, **kwargs):
        """Return a coroutine to be scheduled by the main event loop
        This does not automatically start the coroutine. To start this timer
        pass it to the asyncio.main() function or create a task and schedule
        it to be run

        Example
        -------
        if asyncio.get_event_loop() is None:
            # There is no running event loop
            asyncio.run(recurring_timer.start())

        else:
            # There is an existing event loop
            # AKA working in ipython
            loop = asyncio.get_event_loop()
            if loop.is_running():
                coroutine = recurring_timer.start()
                client_task = asyncio.create_task(coroutine)

            else:
                pass"""
        return self._cycle(*args, **kwargs)

    def is_task_running(self):
        return not self._task.done()



class BufferedSMTPHandler(BufferingHandler):

    def __init__(self, capacity, mailhost, fromaddr, toaddrs, subject,
                 credentials=None, secure=None, timeout=5.0):
        super().__init__(capacity)

        if isinstance(mailhost, (list, tuple)):
            self.mailhost, self.mailport = mailhost
        else:
            self.mailhost, self.mailport = mailhost, None
        if isinstance(credentials, (list, tuple)):
            self.username, self.password = credentials
        else:
            self.username = None
        self.fromaddr = fromaddr
        if isinstance(toaddrs, str):
            toaddrs = [toaddrs]
        self.toaddrs = toaddrs
        self.subject = subject
        self.secure = secure
        self.timeout = timeout

        return

    def flush(self):
        """Reimplement the flush method of BufferingHandler
        This method is called if self.shouldFlush returns True
        shouldFlush is true when the buffer is greater than the threshold

        Emit a record.
        Format the record and send it to the specified addressees.
        """

        try:
            import smtplib
            from email.message import EmailMessage
            import email.utils

            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port, timeout=self.timeout)
            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(None)
            msg['Date'] = email.utils.localtime()
            body = str()
            for record in self.buffer:
                body = body + self.format(record) + '\r\n\r\n'
            msg.set_content(body)
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
            smtp.quit()
        except Exception:
            self.handleError(record)

        return

    def getSubject(self, record):
        """
        Determine the subject for the email.
        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        return self.subject


    def close(self):
        """
        Close the handler.
        This version only flushes the buffer if the buffer is half of capacity.
        Finally, chain the parent class' close().
        """
        try:
            if len(self.buffer) > self.capacity // 2:
                self.flush()
        finally:
            logging.Handler.close(self)

