# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 17:11:46 2020

@author: z003vrzk
"""


# Python imports
import threading
import json
import zlib
import time
import unittest
from socketserver import TCPServer, ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

# Third party imports
import requests

# favorite icon
favicon = zlib.decompress(
    b'x\x9c\xab\x983\n\x90\x00\x00\x9b,\xa5\x01'
    )


#%%


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


class ThreadedHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(b"Content-type", "text/html")
        self.end_headers()
        return None

    def do_GET(self):
        # parse query data and params to find out what was passed
        parsed_params = urlparse(self.path)
        parsed_query = parse_qs(parsed_params.query)

        # find the pieces
        args = parsed_params.path.split("/")

        if args[1] == "read":
            print("Sending response and header")
            self.send_response(200)
            print("Starting long running process")
            self.do_read(args[2:])

        elif args[1] == "whois":
            self.send_response(200)
            self.do_whois(args[2:])

        elif args[1] == "favicon.ico":
            self.send_response(200)
            self.send_header("Content-type", "image/x-icon")
            self.send_header("Content-Length", len(favicon))
            self.end_headers()
            self.wfile.write(favicon)

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Page Title.</title></head>", 'utf-8'))
            self.wfile.write(bytes("<body><p>This is a test</p>", 'utf-8'))
            self.wfile.write(b"<p>'read' or 'whois' expected</p>")
            self.wfile.write(bytes("<p>You tried to access {}".format(self.path), 'utf-8'))
            self.wfile.write(bytes("<p>Serving from thread {}".format(threading.currentThread().getName()), 'utf-8'))
            self.wfile.write(bytes("</body></html>", 'utf-8'))
        return None

    def do_read(self, args):

        # Some process
        time.sleep(3)
        # Make up a result
        result = {'value':float(2394e-22)}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.send_header(b"Content-type", "application/json")
        self.end_headers()
        self.wfile.write(result_bytes)

        return

    def do_whois(self, args):

        # Blah Blah running code
        time.sleep(3)

        # Pretend there is a result
        result = {'device1':{'instance':32415,'objectname':'Foo'}}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.send_header(b"Content-type", "application/json")
        self.end_headers()
        self.wfile.write(result_bytes)
        return



class ThreadedHTTPRequestHandlerTest(unittest.TestCase):

    def setUp(self):
        global HOST, PORT, server, server_thread
        HOST, PORT = 'localhost','8084'

        # local host, special port
        server = ThreadedTCPServer((HOST, int(PORT)), ThreadedHTTPRequestHandler)

        # Start a thread to handle a single request
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.setName('Thread<TCPServer on {}:{}>'.format(HOST,PORT))

        # exit the server thread when the main thread terminates
        server_thread.daemon = True # Exit when program terminates
        server_thread.start()

        print("Initializing server in thread {}".format(server_thread.getName()))
        print("Thread is Alive : ", server_thread.is_alive())

        return

    def tearDown(self):
        # stop servce_forever loop and wait until it stops
        server.shutdown()
        # Clean up the server - Release socket
        server.server_close()

    def test_GET_read(self):
        url = 'http://{}:{}/read'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=10)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'value': 2.394e-19})

        return

    def test_GET_whois(self):
        url = 'http://{}:{}/whois'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=4)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'device1': {'instance': 32415, 'objectname': 'Foo'}})
        return

    def test_GET_favicon(self):
        url = 'http://{}:{}/favicon.ico'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 200)
        return

    def test_GET_404(self):
        url = 'http://{}:{}/bad-url'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 404)
        return






#%%





class TestHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header(b"Content-type", "text/html")
        self.end_headers()
        return None

    def _debug(self):
        # Debugging
        print("Testing")
        print("path:\n", self.path, '\n')
        print("headers:\n", self.headers, '\n')
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        print("body:\n", body, '\n')

        # Print current thread for help
        cur_thread = threading.current_thread()
        print("Current Thread: ", cur_thread, '\n')
        return

    def do_GET(self):
        """
        Example
        """
        # Debug prints
        self._debug()

        # find the pieces
        parsed_params = urlparse(self.path)
        args = parsed_params.path.split("/")
        print("parsed_params:", parsed_params, '\n')
        print("arguments:", args, '\n')

        # Response
        if args[1] == "good-url":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b"Received GET Request\n")
            self.wfile.write(bytes(str(self.path) + '\n', 'utf-8'))
            self.wfile.write(
                bytes(json.dumps({'response':'some-data'}), 'utf-8')
                )
        elif args[1] == 'change-response':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

            # Whoops - change the response code after an error occurs
            self.send_response(404)
            self.wfile.write(b'Changed Response')

        elif args[1] == 'favicon.ico':
            self.send_response(200)
            self.send_header("Content-type", "image/x-icon")
            self.send_header("Content-Length", len(favicon))
            self.end_headers()
            self.wfile.write(b'xxxx')

        elif args[1] == 'change-header':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

            # What happens if I send multiple headers?
            # The response line, headers, and content is simply written
            # To do the socket and appears as if it were in the body
            # Of the response
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'Changed Header')

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Improper URL\n")
            msg = bytes('Got {}'.format(self.path), 'utf-8')
            self.wfile.write(msg)

        return

class basicHttpServerTest(unittest.TestCase):

    def setUp(self):
        global HOST, PORT, server, server_thread
        HOST, PORT = 'localhost','8084'

        # local host, special port
        server = TCPServer((HOST, int(PORT)), TestHTTPRequestHandler)

        # Start a thread to handle a single request
        server_thread = threading.Thread(target=server.serve_forever)

        # exit the server thread when the main thread terminates
        server_thread.daemon = True # Exit when program terminates
        server_thread.start()
        print("Thread is Alive : ", server_thread.is_alive())

        return

    def tearDown(self):
        # stop servce_forever loop and wait until it stops
        server.shutdown()
        # Clean up the server - Release socket
        server.server_close()

    def test_GET_bad_url(self):

        # The headers or body are not re-written after the HTTP 102 response
        # Is sent
        url = 'http://{}:{}/bad-url'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.content, b'Improper URL\nGot /bad-url')

    def test_GET_good_url(self):

        # The headers or body are not re-written after the HTTP 102 response
        # Is sent
        url = 'http://{}:{}/good-url'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        test_response = b'Received GET Request\n/good-url\n{"response": "some-data"}'
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, test_response)
        return

    def test_change_response(self):
        # The headers or body are not re-written after the HTTP 102 response
        # Is sent
        url = 'http://{}:{}/change-response'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        test_response = b'Received GET Request\n/good-url\n{"response": "some-data"}'
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.content, test_response)
        return

    def test_change_header(self):
        url = 'http://{}:{}/change-header'.format(HOST, PORT)
        headers = {'Content-Type':'application/json',
                   }
        test_response = b'Changed Header'
        res = requests.get(url, headers=headers, timeout=2)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, test_response)

        return

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(basicHttpServerTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

