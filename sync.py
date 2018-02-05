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
DEFAULT_OAUTH_TOKEN = os.environ.get('GITHUB_OAUTH_TOKEN')
DEFAULT_CLONE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'repos')
ORGANIZATION = 'mock-apertium'

# meta repo name => repo topics (repos with these topics will be contained in the meta-repo)
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


def sync_metarepo(clone_dir, name, submodules):
    # Clone
    logging.info('Updating meta repository %s with %d submodules', name, len(submodules))
    if not os.path.isdir(os.path.join(clone_dir, name)):
        logging.info('Cloning meta repository %s', name)
        subprocess.check_call(
            shlex.split('git clone --recursive -j8 git@github.com:{}/{}.git'.format(ORGANIZATION, name)),
            cwd=clone_dir)
    else:
        logging.debug('Meta repository %s already cloned', name)

    # Update
    logging.info('Updating meta repository %s', name)
    metarepo_dir = os.path.join(clone_dir, name)
    subprocess.check_call(shlex.split('git pull --ff-only'), cwd=metarepo_dir)
    subprocess.check_call(shlex.split('git submodule update --recursive --remote'), cwd=metarepo_dir)
    changeset = subprocess.check_output(shlex.split('git diff --name-only'), cwd=metarepo_dir, universal_newlines=True).splitlines()
    logging.debug('Changeset is:\n%s', pprint.pformat(changeset, indent=2))
    submodule_changeset = list(filter(lambda change: change in submodules, changeset))
    logging.debug('Submodule changeset is:\n%s', pprint.pformat(submodule_changeset, indent=2))
    logging.info('Meta repository %s saw %d updated submodules', name, len(submodule_changeset))

    # Add / Remove Submodules
    submodule_list_output = subprocess.check_output(
        shlex.split('git config --file .gitmodules --name-only --get-regexp path'),
        cwd=metarepo_dir, universal_newlines=True)
    submodules_present = set(map(lambda line: line.split('.')[1], submodule_list_output.splitlines()))
    submodules_missing = submodules - submodules_present
    submodules_extra = submodules_present - submodules
    logging.info('Meta repository %s has extra submodules %s and missing submodules %s', name, submodules_extra, submodules_missing)

    for submodule in submodules_extra:
        logging.debug('Removing submodule %s from meta repository %s', submodule, name)
        subprocess.check_call(shlex.split('git submodule deinit -f {}'.format(submodule), cwd=metarepo_dir))
        subprocess.check_call(shlex.split('rm -rf .git/modules/{}'.format(submodule), cwd=metarepo_dir))
        subprocess.check_call(shlex.split('git rm -f {}'.format(submodule), cwd=metarepo_dir))

    for submodule in submodules_missing:
        logging.debug('Adding submodule %s to meta repository %s', submodule, name)
        subprocess.check_call(
            shlex.split('git submodule add -b master git@github.com:{}/{}.git'.format(ORGANIZATION, submodule)),
            cwd=metarepo_dir)

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
        subprocess.check_call(shlex.split('git commit -a -m "{}"'.format(commit_message)), cwd=metarepo_dir)
        subprocess.check_call(shlex.split('git push'), cwd=metarepo_dir)
    else:
        logging.info('Meta repository %s requires no changes', name)


def handle_event(args, payload):
    repos = list_repos(args.token)
    repos_by_topic = group_repos_by_topic(repos)
    for name, topics in REPOS.items():
        # submodules = all repos that have any of the topics required to be in any meta-repo
        submodules = functools.reduce(operator.or_, map(lambda topic: set(repos_by_topic[topic]), topics))
        sync_metarepo(args.dir, name, submodules)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            payload = json.loads(self.rfile.read(length))
            logging.debug('Recieved payload:\n%s', pprint.pformat(payload, indent=2))
            event = self.headers['X-Github-Event']
            if event in {'push', 'repository'}:
                handle_event(self.server.args, payload)
                self.send_response(200)
            else:
                logging.warn('Ignoring %s event', event)
                self.send_response(501)
        except Exception as error:
            logging.error('Error while handling payload %s', error, exc_info=True)
            self.send_response(500)
        finally:
            self.send_header('Content-type', 'text/plain')
            self.end_headers()


class PortReuseTCPServer(socketserver.TCPServer):
    def __init__(self, cli_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = cli_args

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def start_server(args):
    global httpd
    httpd = PortReuseTCPServer(args, ('', args.port), RequestHandler)
    logging.info('Starting server on port %d', args.port)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Sync Apertium meta repositories.')
    parser.add_argument(
        'action',
        choices={'startserver', 'sync'},
        help='use "startserver" to start the server and "sync --repo [name]" to force a meta-repo sync',
    )
    parser.add_argument('--verbose', '-v', action='count', help='add verbosity (maximum -v -v)', default=0)
    parser.add_argument('--dir', '-d', help='directory to clone meta repos', default=DEFAULT_CLONE_DIR)
    parser.add_argument('--repo', '-r', help='meta-repo to sync (required with sync action)')
    parser.add_argument('--port', '-p', type=int, help='server port (default: {})'.format(DEFAULT_PORT), default=DEFAULT_PORT)
    parser.add_argument('--token', '-t', help='GitHub OAuth token', required=(DEFAULT_OAUTH_TOKEN is None), default=DEFAULT_OAUTH_TOKEN)
    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        level=levels[min(len(levels) - 1, args.verbose)]
    )

    os.makedirs(args.dir, exist_ok=True)

    if args.action == 'startserver':
        start_server(args)
    elif args.action == 'sync':
        if not args.repo:
            raise argparse.ArgumentError('--repo required with sync action')
        repos = list_repos(args.token)
        repos_by_topic = group_repos_by_topic(repos)
        topics = REPOS[args.repo]
        # submodules = all repos that have any of the topics required to be in this meta-repo (in args.repo)
        submodules = functools.reduce(operator.or_, map(lambda topic: set(repos_by_topic[topic]), topics))
        sync_metarepo(args.dir, args.repo, submodules)


if __name__ == '__main__':
    main()
