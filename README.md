# Apertium on Github

## Proposal

See [PMC_proposals/Move_Apertium_to_Github](http://wiki.apertium.org/wiki/PMC_proposals/Move_Apertium_to_Github).

## Structure

- Each package will have its own repository.
- "Meta repositories" will contain only submodules.
  - `apertium-all` will be the root repo, containing repos with topics `apertium-core` and `apertium-all` (the latter are the repos below).
  - `apertium-tools` will contain tools (repos with topic `apertium-tools`).
  - `apertium-staging` will contain staging language pairs (repos with topic `apertium-staging`).
  - `apertium-nursery` will contain nursery language pairs (repos with topic `apertium-nursery`).
  - `apertium-incubator` will contain staging language modules/pairs (repos with topic `apertium-incubator`).
  - `apertium-trunk` will contain trunk language modules/pairs (repos with topic `apertium-trunk`).
- Meta repositories will be kept up-to-date by `sync.py` (described below).
- SVN external properties will be used to maintain some backwards compatability.

**N.B.** The topics (a.k.a. tags) are integral.

## Transition

### Organization

When created, all package repositories (pairs/languages/tools) will belong to
the [apertium GitHub organization][2]. Members of the PMC will be 'owners' of
this organization and all other Apertium contributors will be 'members', with
[these permissions][1].

Each repository will have the following [permission levels][3]:

- 'owner': (same for all packages) PMC members
- 'admin': (package-specific) one or more 'package maintainers' who will merge
           pull requests, change continuous integration settings, etc.
- 'write': (package-specific) Apertium contributors who have been given commit
           access
- 'read': (same for all packages) any GitHub user

The meta-repositories `apertium-all`, `apertium-tools`, `apertium-staging`,
`apertium-nursery`, `apertium-incubator`, and `apertium-trunk` should be
['pinned repositories'][4] for the organization so that they are at the top of
the list of repositories when a user lands on the organization page.

Note that nobody should have write permissions for these meta-repositories,
except owners of course. Their contents will, for the most part, be updated
automatically via [`sync.py`][5].

### Scripts

These scripts rely on [SubGit][6] being present in the current (top) directory
and use the `svn_authors.txt` file to convert
SVN users to GitHub emails to establish connections between commits and
GitHub accounts. Utility functions are located in `util.sh`.

- `import-repo.sh "svn-url" "github-repo-name" '["github-topic-1", "github-topic-2", ...]'`
  will import the SVN repo at `svn-url` to GitHub with the name
  `github-repo-name` and the given (possibly only one) topics.
- `import-modules.sh` imports all language pairs, modules, and the Apertium core
  from SVN to Github.
- `create-metarepos.sh` creates all the mono-repos and syncs their submodules

For the actual migration, an owner of the [apertium GitHub organization][2]
needs to:

1. Create a [GitHub OAuth token][7] with 'repo' permissions.
1. Run `export GITHUB_OAUTH_TOKEN=<token from above>` to set the environment variable.
1. Download and unzip [SubGit][6] in the current directory.
1. Edit line 5 of `util.sh` with their own GitHub username and line 6 with `apertium`.
1. Run `./import-modules.sh`.
1. Run `./create-metarepos.sh`.

- TODO: svn propset script

## Maintenance

- [`sync.py`][5] recieves events from GitHub web hooks.
- Any updates to repositories with the appropriate tags will be pushed to the appropriate meta-repository.
- New repositories with a valid topic will be added to the appropriate meta-repository.
- Deleted repositories with a valid topic will be deleted from the appropriate meta-repository.

Usage:

    usage: sync.py [-h] [--verbose] [--dir DIR] [--repo REPO] [--port PORT]
                  [--token TOKEN] [--sync-interval SYNC_INTERVAL]
                  {startserver,sync}

    Sync Apertium meta repositories.

    positional arguments:
      {startserver,sync}    use "startserver" to start the server and "sync --repo
                            [name]" to force a meta-repo sync

    optional arguments:
      -h, --help            show this help message and exit
      --verbose, -v         add verbosity (maximum -vv)
      --dir DIR, -d DIR     directory to clone meta repos
      --repo REPO, -r REPO  meta-repo to sync (required with sync action)
      --port PORT, -p PORT  server port (default: 9712)
      --token TOKEN, -t TOKEN
                            GitHub OAuth token
      --sync-interval SYNC_INTERVAL, -i SYNC_INTERVAL
                            min interval between syncs (default: 3s)

The GitHub OAuth token is described in the 'Scripts' section above. For
`sync.py`, it can also be set through the environment variable
`GITHUB_OAUTH_TOKEN`.

## Interface

We provide a wrapper on top of GitHub's organization view since it only supports
pinning up to six repositories, searching is cumbersome and there are no custom
layout options.

The source for this interface is `source-browser.html`. For the sake of simplicity,
only modern browsers are supported. It is made available via
[GH pages](https://sushain97.github.io/apertium-on-github/source-browser.html).

## Helpful Git Commands

- Remember, [`git svn`](https://git-scm.com/book/en/v1/Git-and-Other-Systems-Git-and-Subversion) is always an option and offers an bona fide SVN experience.
- Kernel.org's [Git for SVN users cheatsheet](https://git.wiki.kernel.org/images-git/7/78/Git-svn-cheatsheet.pdf).
- Meta repository commands
  - To checkout a meta repository, use `git clone --recursive -j8 [url]`.
  - To pull (update) a meta repository, use `git pull --recurse-submodules`. Never use `git submodule update`, you will get conflicts with the sync script's pushes.
  - To push changes to submodules within a meta repository, use `git submodule foreach git push`.
- Use Git [alias](https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases) for any oft used commands.

[1]: https://help.github.com/articles/permission-levels-for-an-organization/
[2]: https://github.com/orgs/apertium/
[3]: https://help.github.com/articles/repository-permission-levels-for-an-organization/
[4]: https://github.com/blog/2191-pin-repositories-to-your-github-profile
[5]: https://github.com/sushain97/apertium-on-github/blob/master/sync.py
[6]: https://subgit.com/
[7]: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
