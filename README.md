Apertium on Github
==================

Proposal
--------

See [PMC_proposals/Move_Apertium_to_Github](http://wiki.apertium.org/wiki/PMC_proposals/Move_Apertium_to_Github).

Structure
---------

- Each package will have its own repository.
- "Meta repositories" will contain only submodules.
  - `apertium-all` will contain repos with topics `apertium-core`, `apertium-tools`, `apertium-staging`, `apertium-incubator`, `apertium-nursery`, `apertium-trunk`.
  - `apertium-tools` will contain tools (repos with topic `apertium-tools`).
  - `apertium-staging` will contain staging language pairs (repos with topic `apertium-staging`).
  - `apertium-nursery` will contain nursery language pairs (repos with topic `apertium-nursery`).
  - `apertium-incubator` will contain staging language modules/pairs (repos with topic `apertium-incubator`).
  - `apertium-trunk` will contain trunk language modules/pairs(repos with topic `apertium-trunk`).
- Meta repositories will be kept up-to-date by `sync.py` (described below).
- SVN external properties will be used to maintain some backwards compatability.

**N.B.** The topics (a.k.a. tags) are integral.

Transition
----------

TODO

Maintenance
-----------

- The `sync.py` recieves events from GitHub web hooks.
- Any updates to repositories with the appropriate tags will be pushed to the appropriate meta-repository.
- New repositories with a valid topic will be added to the appropriate meta-repository.
- Deleted repositories with a valid topic will be deleted from the appropriate meta-repository.

Usage:

    usage: sync.py [-h] [--verbose] [--dir DIR] [--repo REPO] [--port PORT]
                [--token TOKEN]
                {sync,startserver}

    Sync Apertium meta repositories.

    positional arguments:
    {sync,startserver}    use "startserver" to start the server and "sync --repo
                            [name]" to force an sync

    optional arguments:
    -h, --help            show this help message and exit
    --verbose, -v         adjust verbosity
    --dir DIR, -d DIR     directory to clone meta repos
    --repo REPO, -r REPO  repository to sync (required with sync action)
    --port PORT, -p PORT  server port (default: 9712)
    --token TOKEN, -t TOKEN
                            GitHub OAuth token

The GitHub OAuth token can also be set by exporting `GITHUB_OAUTH_TOKEN`:

    export GITHUB_OAUTH_TOKEN=XXX

Interface
---------

We provide a wrapper on top of GitHub's organization view since it only supports
pinning up to six repositories, searching is cumbersome and there are no custom
layout options.

The source for this interface is `source-browser.html`. For the sake of simplicity,
only modern browsers are supported. It is made available via
[GH pages](https://sushain97.github.io/apertium-on-github/source-browser.html).

Helpful Git Commands
--------------------

- Remember, [`git svn`](https://git-scm.com/book/en/v1/Git-and-Other-Systems-Git-and-Subversion) is always an option and offers an bona fide SVN experience.
- Kernel.org's [Git for SVN users cheatsheet](https://git.wiki.kernel.org/images-git/7/78/Git-svn-cheatsheet.pdf).
- Meta repository commands
  - To checkout a meta repository, use `git clone --recursive -j8 [url]`.
  - To pull (update) a meta repository, use `git pull --recurse-submodules`. Never use `git submodule update`, you will get conflicts with the sync script's pushes.
  - To push changes to submodules within a meta repository, use `git submodule foreach git push`.
- Use Git [alias](https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases) for any oft used commands.
