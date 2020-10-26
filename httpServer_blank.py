# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 20:36:08 2020

@author: z003vrzk
"""

# Python imports
import os
import threading
import json
import zlib
import threading

from collections import OrderedDict
import configparser

from urllib.parse import urlparse, parse_qs
from socketserver import ThreadingMixIn, TCPServer
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from http.server import HTTPServer

HOST = 'localhost'
PORT = 8081

#%%



class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class ThreadedHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(b"Content-type", "text/html")
        self.end_headers()
        return None

    def do_GET(self):
        self.send_response(200)
        self.send_header(b"Content-type", "text/html")
        self.end_headers()

        self.wfile.write(bytes("<html><head><title>Page Title.</title></head>", 'utf-8'))
        self.wfile.write(bytes("<body><p>This is a test</p>", 'utf-8'))
        self.wfile.write(bytes("<p>You tried to access {}".format(self.path), 'utf-8'))
        self.wfile.write(bytes("<p>Serving from thread {}".format(threading.currentThread().getName()), 'utf-8'))
        self.wfile.write(bytes("</body></html>", 'utf-8'))

        return None

try:
    server = ThreadedHTTPServer((HOST, PORT), ThreadedHTTPRequestHandler)

    # Start a thread with the server -- that thread will then start a thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.setName('Thread<HTTPServer on {}:{}>'.format(HOST,PORT))
    server_thread.daemon = False # The thread will not automatically close
    print("Initializing server in thread {}".format(server_thread.getName()))
    server_thread.start()
    print("Alive?", server_thread.is_alive())
    print("Alive?", server_thread.isAlive())

except Exception as err:
    print(err)
    raise(err)

finally:
    if server:
        server.shutdown()
        server.server_close() # Release the socket

#%% Create a client and send request as a HTTP request

import requests

url = 'http://{}:{}/read/192.168.1.100/analogValue:0'.format(HOST,PORT)
response = requests.get(url)
response.text
response.status_code

for _ in range(500):
    response = requests.get(url)
    print(response.text)
