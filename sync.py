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
import concurrent.futures
import contextlib
import functools
import http.server
import json
import logging
import operator
import os
import pprint
import queue
import shlex
import signal
import socket
import socketserver
import subprocess
import sys
import textwrap
import threading
import urllib.request

# Each element of this list is a dict from meta repo name to its topics.
# Each meta repo will sync as submodules any repo with at least one of its topics.
# The meta repos within a dict are updated in parallel but each dict is updated in serial.
# Therefore, meta repo B dependent on meta repo A should come in a dict after one with A.
# Each meta repo will be synced on any Push/Repository event unless the event is associated
# directly with any repo in its dict.
METAREPOS = [
    {
        'apertium-incubator': {'apertium-incubator'},
        'apertium-languages': {'apertium-languages'},
        'apertium-nursery': {'apertium-nursery'},
        'apertium-staging': {'apertium-staging'},
        'apertium-tools': {'apertium-tools'},
        'apertium-trunk': {'apertium-trunk'},
    },
    {
        'apertium-all': {'apertium-core', 'apertium-all'},
    },
]
ORGANIZATION = 'mock-apertium'
GITHUB_API = 'https://api.github.com/graphql'

DEFAULT_PORT = 9712
DEFAULT_OAUTH_TOKEN = os.environ.get('GITHUB_OAUTH_TOKEN')
DEFAULT_CLONE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'repos')
DEFAULT_SYNC_INTERVAL = 3  # seconds

server = None


def close_socket():
    global server
    if server:
        logging.info('Stopping server')
        server.server_close()
        server = None
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
            organization(login: "%s") {
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
          }''') % (ORGANIZATION, (', after: "{}"'.format(after) if after else ''))
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
    logging.debug('Feched repositories:\n%s', pprint.pformat(repos, indent=2))
    return repos


def group_repos_by_topic(repos):
    groups = collections.defaultdict(list)
    for repo in repos:
        name = repo['node']['name']
        for topicNode in repo['node']['repositoryTopics']['nodes']:
            groups[topicNode['topic']['name']].append(name)
    logging.debug('Grouped repositories:\n%s', pprint.pformat(groups, indent=2))
    return groups


def repos_for_topics(repos_by_topic, topics):
    return functools.reduce(operator.or_, map(lambda topic: set(repos_by_topic[topic]), topics))


def sync_metarepo(clone_dir, name, submodules):
    # Clone
    logging.info('Updating meta repository %s with %d submodules', name, len(submodules))
    if not os.path.isdir(os.path.join(clone_dir, name)):
        logging.info('Cloning meta repository %s', name)
        subprocess.check_call(shlex.split('git clone --recursive --jobs 8 git@github.com:{}/{}.git'.format(ORGANIZATION, name)), cwd=clone_dir)
    else:
        logging.debug('Meta repository %s already cloned', name)

    # Update
    logging.info('Updating meta repository %s', name)
    metarepo_dir = os.path.join(clone_dir, name)
    metarepo_check_call = functools.partial(subprocess.check_call, cwd=metarepo_dir)
    metarepo_check_call(shlex.split('git pull --ff-only'))
    metarepo_check_call(shlex.split('git submodule update --jobs 8 --remote'))
    changeset = subprocess.check_output(shlex.split('git diff --name-only'), cwd=metarepo_dir, universal_newlines=True).splitlines()
    logging.debug('Changeset is: %s', changeset)
    submodule_changeset = list(filter(lambda change: change in submodules, changeset))
    logging.debug('Submodule changeset is: %s', submodule_changeset)
    logging.info('Meta repository %s saw %d updated submodules', name, len(submodule_changeset))

    # Add / Remove Submodules
    submodule_list_output = subprocess.check_output(
        shlex.split('git config --file .gitmodules --name-only --get-regexp path'),
        cwd=metarepo_dir,
        universal_newlines=True,
    )
    submodules_present = set(map(lambda line: line.split('.')[1], submodule_list_output.splitlines()))
    submodules_missing = submodules - submodules_present
    submodules_extra = submodules_present - submodules
    logging.info('Meta repository %s has extra submodules %s and missing submodules %s', name, submodules_extra, submodules_missing)

    for submodule in submodules_extra:
        logging.debug('Removing submodule %s from meta repository %s', submodule, name)
        metarepo_check_call(shlex.split('git submodule deinit --force {}'.format(submodule)))
        metarepo_check_call(shlex.split('rm -rf .git/modules/{}'.format(submodule)))
        metarepo_check_call(shlex.split('git rm --force {}'.format(submodule)))

    for submodule in submodules_missing:
        logging.debug('Adding submodule %s to meta repository %s', submodule, name)
        metarepo_check_call(shlex.split('git submodule add --branch master git@github.com:{}/{}.git'.format(ORGANIZATION, submodule)))

    # Commit and Push
    clean = subprocess.call(shlex.split('git diff-index --quiet HEAD --'), cwd=metarepo_dir) == 0
    if not clean:
        logging.info('Pushing changes to meta repository %s', name)
        commit_message = textwrap.dedent('''
            Sync submodules
            Updated: {}.
            Deleted: {}.
            Added: {}.
        '''.format(
            ', '.join(submodule_changeset) or 'None',
            ', '.join(submodules_extra) or 'None',
            ', '.join(submodules_missing) or 'None',
        ))
        logging.debug('Meta repository %s commit message:\n%s', name, pprint.pformat(commit_message, indent=2))
        metarepo_check_call(shlex.split('git commit --all --message "{}"'.format(commit_message)))
        metarepo_check_call(shlex.split('git push'))
    else:
        logging.info('Meta repository %s requires no changes', name)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            payload = json.loads(self.rfile.read(length))
            logging.debug('Recieved payload:\n%s', pprint.pformat(payload, indent=2))
            event = self.headers['X-Github-Event']
            if event in {'push', 'repository'}:
                self.server.event_queue.put(payload)
                self.send_response(200)
            else:
                logging.warn('Ignoring %s event', event)
                self.send_response(501)
        except Exception as error:
            logging.error('Error while handling payload %s', error, exc_info=True)
            self.send_response(500)
        finally:
            self.end_headers()


class Server(socketserver.TCPServer):
    def __init__(self, cli_args, event_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = cli_args
        self.event_queue = event_queue
        self.event_handler_timer = threading.Timer(self.args.sync_interval, self.handle_events)
        self.event_handler_timer.start()

    def handle_events(self):
        # wait for an event
        self.event_queue.get()
        logging.info('Starting meta repository update')

        # discard any other piled up events
        while not self.event_queue.empty():
            with contextlib.suppress(queue.Empty):
                self.event_queue.get_nowait()
                self.event_queue.task_done()

        # update the meta repos and block until completion
        repos = list_repos(self.args.token)
        repos_by_topic = group_repos_by_topic(repos)
        for metarepos in METAREPOS.topics():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                for name, topics in metarepos.items():
                    submodules = repos_for_topics(repos_by_topic, topics)
                    pool.submit(sync_metarepo, self.args.dir, name, submodules)

        # mark as complete and schedule next handler
        self.event_queue.task_done()
        logging.info('Scheduling next meta repository update')
        self.event_handler_timer = threading.Timer(self.args.sync_interval, self.handle_events).start()

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def server_close(self):
        self.event_handler_timer.cancel()


def start_server(args):
    global server
    logging.info('Starting server on port %d', args.port)
    event_queue = queue.Queue()
    server = Server(args, event_queue, ('', args.port), RequestHandler)
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Sync Apertium meta repositories.')
    parser.add_argument(
        'action',
        choices={'startserver', 'sync'},
        help='use "startserver" to start the server and "sync --repo [name]" to force a meta-repo sync',
    )
    parser.add_argument('--verbose', '-v', action='count', help='add verbosity (maximum -vv)', default=0)
    parser.add_argument('--dir', '-d', help='directory to clone meta repos', default=DEFAULT_CLONE_DIR)
    parser.add_argument('--repo', '-r', help='meta-repo to sync (required with sync action)', choices=list(collections.ChainMap(*METAREPOS).keys()))
    parser.add_argument('--port', '-p', type=int, help='server port (default: {})'.format(DEFAULT_PORT), default=DEFAULT_PORT)
    parser.add_argument('--token', '-t', help='GitHub OAuth token', required=(DEFAULT_OAUTH_TOKEN is None), default=DEFAULT_OAUTH_TOKEN)
    parser.add_argument('--sync-interval', '-i', help='min interval between syncs (default: {}s)'.format(DEFAULT_SYNC_INTERVAL), default=DEFAULT_SYNC_INTERVAL)
    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        level=levels[min(len(levels) - 1, args.verbose)],
    )

    os.makedirs(args.dir, exist_ok=True)

    if args.action == 'startserver':
        start_server(args)
    elif args.action == 'sync':
        if not args.repo:
            raise argparse.ArgumentError('--repo required with sync action')
        repos = list_repos(args.token)
        repos_by_topic = group_repos_by_topic(repos)
        topics = collections.ChainMap(*METAREPOS)[args.repo]
        submodules = repos_for_topics(repos_by_topic, topics)
        sync_metarepo(args.dir, args.repo, submodules)


if __name__ == '__main__':
    main()
