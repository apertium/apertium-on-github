#!/usr/bin/env python3
'''
    Syncs submodules within Apertium meta-repositories.
    Assumes that the Content type of payloads is `application/json`.
    Requires all `Push` and `Repository` events.
'''

__author__ = "Sushain K. Cherivirala"
__version__ = "0.1.0"
__license__ = "GPLv3+"

import argparse
import atexit
import http.server
import logging
import signal
import socket
import socketserver
import sys

DEFAULT_PORT = 9712
# repo name => topics
REPOS = {
    'apertium-languages': {'languages'},
    'apertium-staging': {'staging'}
}

httpd = None


def close_socket():
    global httpd
    if httpd:
        logging.info('Stopping server')
        httpd.server_close()
        httpd = None
        sys.exit(0)


atexit.register(close_socket)


def signal_handler(signal, frame):
    close_socket()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            payload = self.rfile.read(length)
            logging.debug('Recieved payload %s', payload)
            # TODO: handle push
            # TODO: handle repo rename?
            # TODO: handle new repo
            # TODO: handle repo delete
            # TODO: clone repo and allow configuring where
            self.send_response(200)
        except Exception as error:
            logging.error('Error while handling payload %s', error, exc_info=True)
            self.send_response(500)


class PortReuseTCPServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def start_server(port):
    global httpd
    httpd = PortReuseTCPServer(('', port), RequestHandler)
    logging.info('Starting server on port %d', port)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Sync Apertium meta repositories.')
    parser.add_argument(
        'action',
        choices={'startserver', 'update'},
        help='Use "startserver" to start the server and "update" to force an update',
    )
    parser.add_argument('--verbose', '-v', action='count', help='Adjust verbosity', default=0)
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        level=levels[min(len(levels) - 1, args.verbose)]
    )

    if args.action == 'startserver':
        start_server(args.port)
    elif args.action == 'update':
        raise NotImplementedError()  # TODO: implement this


if __name__ == '__main__':
    main()
