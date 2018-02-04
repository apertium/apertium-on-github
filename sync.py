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
import collections
import functools
import http.server
import json
import logging
import operator
import os
import pprint
import shlex
import signal
import socket
import socketserver
import subprocess
import sys
import textwrap
import urllib.request

GITHUB_API = 'https://api.github.com/graphql'
DEFAULT_PORT = 9712
DEFAULT_CLONE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'repos')
# meta repo name => topics of the repos it should contain
ORGANIZATION = 'mock-apertium'
REPOS = {
    'apertium-all': {
        'apertium-core',
        'apertium-incubator',
        'apertium-languages',
        'apertium-nursery',
        'apertium-staging',
        'apertium-tools',
        'apertium-trunk',
    },
    'apertium-incubator': {'apertium-incubator'},
    'apertium-languages': {'apertium-languages'},
    'apertium-nursery': {'apertium-nursery'},
    'apertium-staging': {'apertium-staging'},
    'apertium-tools': {'apertium-tools'},
    'apertium-trunk': {'apertium-trunk'},
}
DEFAULT_OAUTH_TOKEN = os.environ.get('GITHUB_OAUTH_TOKEN')

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


def _list_repos(token, after=None):
    headers = {
        'Authorization': 'bearer {}'.format(token),
    }
    request_data = json.dumps({
        'query': textwrap.dedent('''
          {
            organization(login: "mock-apertium") {
              repositories(first: 100%s) {
                edges {
                  node {
                    name
                    repositoryTopics(first: 50) {
                      nodes {
                        topic {
                          name
                        }
                      }
                    }
                  }
                }
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
            }
          }''' % (', after: "{}"'.format(after) if after else ''))
    }).encode("utf-8")
    request = urllib.request.Request(GITHUB_API, data=request_data, headers=headers)
    response = urllib.request.urlopen(request).read()
    data = json.loads(response)['data']
    repos = data['organization']['repositories']
    if repos['pageInfo']['hasNextPage']:
        logging.debug('Fetched list of %d repositories, continuing to next page', len(repos['edges']))
        return repos['edges'] + _list_repos(token, after=repos['pageInfo']['endCursor'])
    else:
        logging.debug('Fetched list of %d repositories, query complete', len(repos['edges']))
        return repos['edges']


def list_repos(token):
    logging.info('Listing repositories')
    repos = _list_repos(token, after=None)
    logging.info('Fetched list of %d repositories', len(repos))
    logging.debug('Feched repositories: %s', pprint.pformat(repos, indent=2))
    return repos


def group_repos_by_topic(repos):
    groups = collections.defaultdict(list)
    for repo in repos:
        name = repo['node']['name']
        for topicNode in repo['node']['repositoryTopics']['nodes']:
            groups[topicNode['topic']['name']].append(name)
    logging.debug('Grouped repositories: %s', groups)
    return groups


def update_metarepo(clone_dir, name, submodules):
    if not os.path.isdir(os.path.join(clone_dir, name)):
        logging.info('Cloning meta repository %s', name)
        args = shlex.split('git clone --recursive -j8 git@github.com:{}/{}.git'.format(ORGANIZATION, name))
        subprocess.check_call(args, cwd=clone_dir)
    else:
        logging.debug('Meta repository %s already cloned', name)
    subprocess.check_call(args)
    print(clone_dir, name, submodules)


def handle_event(args, payload):
    repos = list_repos(args.token)
    repos_by_topic = group_repos_by_topic(repos)
    for name, topics in REPOS.items():
        submodules = functools.reduce(operator.or_, map(lambda topic: set(repos_by_topic[topic]), topics))
        update_metarepo(args.dir, name, submodules)


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, args):
        self.args = args

    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            payload = json.loads(self.rfile.read(length))
            logging.debug('Recieved payload %s', pprint.pformat(payload, indent=2))
            event = self.headers['X-Github-Event']
            if event in {'push', 'repository'}:
                handle_event(self.args, payload)
            else:
                logging.warn('Ignoring %s event', event)
            self.send_response(200)
            self.end_headers()
        except Exception as error:
            logging.error('Error while handling payload %s', error, exc_info=True)
            self.send_response(500)
            self.end_headers()


class PortReuseTCPServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def start_server(args):
    global httpd
    httpd = PortReuseTCPServer(('', args.port), RequestHandler(args))
    logging.info('Starting server on port %d', args.port)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Sync Apertium meta repositories.')
    parser.add_argument(
        'action',
        choices={'startserver', 'update'},
        help='Use "startserver" to start the server and "update --repo [name]" to force an update',
    )
    parser.add_argument('--verbose', '-v', action='count', help='Adjust verbosity', default=0)
    parser.add_argument('--dir', '-d', help='Directory to clone meta repos', default=DEFAULT_CLONE_DIR)
    parser.add_argument('--repo', '-r', help='Repository to update (required with update action)')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT)
    parser.add_argument('--token', '-t', help='GitHub OAuth token', required=(DEFAULT_OAUTH_TOKEN is None), default=DEFAULT_OAUTH_TOKEN)
    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        level=levels[min(len(levels) - 1, args.verbose)]
    )

    os.makedirs(args.dir, exist_ok=True)

    update_metarepo(args.dir, 'apertium-staging', [])
    return

    if args.action == 'startserver':
        start_server(args)
    elif args.action == 'update':
        if not args.repo:
            raise argparse.ArgumentError('--repo required with update action')
        update_metarepo(args, args.repo)


if __name__ == '__main__':
    main()
