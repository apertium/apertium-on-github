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
import shutil
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
# The meta repos within a dict are synced in parallel but each dict is synced in serial.
# Therefore, meta repo B dependent on meta repo A should come in a dict after one with A.
# Each meta repo will be synced on any Push/Repository event unless the event is associated
# directly with any repo in its dict or a dict after it.
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
    response = urllib.request.urlopen(request).read().decode('utf-8')
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


class MetaRepoSyncer:
    def __init__(self, clone_dir, name, submodules):
        self.clone_dir = clone_dir
        self.name = name
        self.submodules = submodules
        self.dir = os.path.join(clone_dir, name)
        self.check_call = functools.partial(subprocess.check_call, cwd=self.dir)

    def clone(self, init_submodules=True):
        if not os.path.isdir(os.path.join(self.clone_dir, self.name)):
            logging.info('Cloning meta repository %s', self.name)
            subprocess.check_call(shlex.split('git clone git@github.com:{}/{}.git'.format(ORGANIZATION, self.name)), cwd=self.clone_dir)
            if init_submodules:
                self.check_call(shlex.split('git submodule update --init --jobs 8'))
        else:
            logging.debug('Meta repository %s already cloned', self.name)

    def update(self):
        self.check_call(shlex.split('git pull --rebase --autostash'))
        self.check_call(shlex.split('git submodule update --jobs 8 --remote'))
        changeset = subprocess.check_output(shlex.split('git diff --name-only'), cwd=self.dir, universal_newlines=True).splitlines()
        logging.debug('Changeset is: %s', changeset)
        submodule_changeset = list(filter(lambda change: change in self.submodules, changeset))
        logging.debug('Submodule changeset is: %s', submodule_changeset)
        logging.info('Meta repository %s has %d updated submodules', self.name, len(submodule_changeset))
        return submodule_changeset

    def list_submodules_present(self):
        if os.path.exists(os.path.join(self.dir, '.gitmodules')):
            submodule_list_output = subprocess.check_output(
                shlex.split('git config --file .gitmodules --name-only --get-regexp path'),
                cwd=self.dir,
                universal_newlines=True,
            )
            return set(map(lambda line: line.split('.')[1], submodule_list_output.splitlines()))
        return set()

    def add_submodules(self, submodules_present):
        submodules_missing = self.submodules - submodules_present
        for submodule in submodules_missing:
            logging.debug('Adding submodule %s to meta repository %s', submodule, self.name)
            self.check_call(shlex.split('git submodule add --branch master git@github.com:{}/{}.git'.format(ORGANIZATION, submodule)))
        return submodules_missing

    def remove_submodules(self, submodules_present):
        submodules_extra = submodules_present - self.submodules
        for submodule in submodules_extra:
            logging.debug('Removing submodule %s from meta repository %s', submodule, self.name)
            self.check_call(shlex.split('git submodule deinit --force -- {}'.format(submodule)))
            self.check_call(shlex.split('git rm --force {}'.format(submodule)))
            self.check_call(shlex.split('rm -rf .git/modules/{}'.format(submodule)))
        return submodules_extra

    def commit(self, submodule_changeset, submodules_extra, submodules_missing):
        clean = subprocess.call(shlex.split('git diff-index --quiet HEAD --'), cwd=self.dir) == 0
        if not clean:
            logging.info('Committing changes to meta repository %s', self.name)
            commit_message = textwrap.dedent('''
                Sync submodules ({0}U, {2}D, {4}A)
                Updated: {1}.
                Deleted: {3}.
                Added: {5}.
            '''.format(
                len(submodule_changeset), ', '.join(submodule_changeset) or 'None',
                len(submodules_extra), ', '.join(submodules_extra) or 'None',
                len(submodules_missing), ', '.join(submodules_missing) or 'None',
            ))
            logging.debug('Meta repository %s commit message: %s', self.name, commit_message)
            self.check_call(shlex.split('git commit --all --message "{}"'.format(commit_message)))
        else:
            logging.info('Meta repository %s requires no changes', self.name)

    def push(self):
        self.check_call(shlex.split('git push'))

    def nuke(self):
        logging.debug('Nuking meta repository %s', self.name)
        shutil.rmtree(self.dir)

    def _sync_with_invalid_submodules(self):
        self.nuke()
        self.clone(init_submodules=False)
        submodules_present = self.list_submodules_present()
        submodules_extra = self.remove_submodules(submodules_present)
        self.commit([], submodules_extra, [])
        self.push()
        self.nuke()
        self.sync(remove_orphans=False)

    def sync(self, remove_orphans=True):
        logging.info('Syncing meta repository %s', self.name)

        try:
            self.clone()
        except subprocess.CalledProcessError as error:
            if remove_orphans:
                logging.warn('Cloning meta repository %s failed, removing invalid submodules: %s', self.name, error, exc_info=True)
                self._sync_with_invalid_submodules()
            else:
                logging.error('Syncing meta repository %s failed after removing invalid submodules: %s', self.name, error, exc_info=True)
            return

        try:
            submodule_changeset = self.update()
        except subprocess.CalledProcessError as error:
            if remove_orphans:
                logging.warn('Updating meta repository %s failed, removing invalid submodules: %s', self.name, error, exc_info=True)
                self._sync_with_invalid_submodules()
            else:
                logging.error('Syncing meta repository %s failed after removing invalid submodules: %s', self.name, error, exc_info=True)
            return

        submodules_present = self.list_submodules_present()
        submodules_extra = self.remove_submodules(submodules_present)
        submodules_missing = self.add_submodules(submodules_present)
        self.commit(submodule_changeset, submodules_extra, submodules_missing)
        self.push()


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
        self.schedule_event_handler()

    def schedule_event_handler(self):
        logging.debug('Scheduling next event handler')
        self.event_handler_timer = threading.Timer(self.args.sync_interval, self.handle_events)
        self.event_handler_timer.daemon = True
        self.event_handler_timer.start()

    def handle_events(self):
        logging.info('Waiting for an event')
        events = []
        events.append(self.event_queue.get())

        while not self.event_queue.empty():
            with contextlib.suppress(queue.Empty):
                events.append(self.event_queue.get_nowait())
                self.event_queue.task_done()

        affected_repos = set(map(lambda event: event['repository']['name'], events))
        logging.debug('Got %d events representing %d repositories: %s', len(events), len(affected_repos), affected_repos)

        logging.info('Starting meta repository sync')
        repos = list_repos(self.args.token)
        repos_by_topic = group_repos_by_topic(repos)
        for i, metarepo_group in enumerate(METAREPOS):
            later_metarepos = set(sum(list(map(lambda group: list(group.keys()), METAREPOS[i + 1:])), []))
            relevant_affected_repos = affected_repos - (later_metarepos | set(metarepo_group.keys()))
            if relevant_affected_repos:
                logging.debug('Relevant affected repositories for group %d are: %s', i, relevant_affected_repos)
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    for name, topics in metarepo_group.items():
                        submodules = repos_for_topics(repos_by_topic, topics)
                        pool.submit(MetaRepoSyncer(self.args.dir, name, submodules).sync)
            else:
                logging.debug('Ignoring events for meta repository group %d', i)

        self.event_queue.task_done()
        self.schedule_event_handler()

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def server_close(self):
        self.event_handler_timer.cancel()
        super().server_close()


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
    parser.add_argument('--repo', '-r', help='meta-repo to sync (default: all)', choices=list(collections.ChainMap(*METAREPOS).keys()))
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
        repos = list_repos(args.token)
        repos_by_topic = group_repos_by_topic(repos)
        if args.repo:
            topics = collections.ChainMap(*METAREPOS)[args.repo]
            submodules = repos_for_topics(repos_by_topic, topics)
            MetaRepoSyncer(args.dir, args.repo, submodules).sync()
        else:
            for metarepo_group in METAREPOS:
                for name, topics in metarepo_group.items():
                    submodules = repos_for_topics(repos_by_topic, topics)
                    MetaRepoSyncer(args.dir, name, submodules).sync()


if __name__ == '__main__':
    main()
