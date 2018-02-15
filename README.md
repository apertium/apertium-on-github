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

#### Members

Initially,

- All package repositories (pairs/languages/tools) will belong to the [apertium GitHub organization][2]. 
- Members of the PMC will be `owners` of this organization.
- All other Apertium contributors will be `members`. The PMC can make someone a `member`
  of the organization with a majority vote.

The permissions associated with these roles are described [in detail][1]. 

`TODO.sh` will invite all the non-SourceForge emails in `svn-authors.txt` 
to the organization as members. For technical reasons, surrounding [rate limits][11],
this script should be run a few days prior to repository migration.

#### Repositories

##### Permissions

Each repository will have the following [permission levels][3]:

- `owner`: (**same for all repositories**) PMC members (same as the organization `owners`). Can do anything.
- `admin`: (**repository-specific**) Organization `members` that serve as 'package maintainers'. The PMC can 
  designate a `member` of the organization as an `admin` with a majority vote. Of particular relevance to 
  Apertium are the following permissions they have in addition to `write` permissions:
  - manage repository settings
  - delete the repository
  - add/delete outside collaborators (people with `write` access who are not Apertium `members`)
  - manage topics (including moving from e.g. staging to trunk)
- `write`: (**repository-specific**) Organization `members` that can commit to the repository. Any PMC
  member can give a `member` of the organization `write` permission to a repository.
- `read`: (**same for all packages**) any GitHub user since our repositories are all public

##### Meta Repositories

The meta-repositories `apertium-all`, `apertium-tools`, `apertium-staging`,
`apertium-nursery`, `apertium-incubator`, and `apertium-trunk` should be
['pinned repositories'][4] for the organization so that they are at the top of
the list of repositories when a user lands on the organization page.

Note that nobody should have write permissions for these meta-repositories,
except owners of course. Their contents will, for the most part, be updated
automatically via [`sync.py`][5].

#### Scripts

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

#### Migration

For the actual migration, an owner of the [apertium GitHub organization][2]
needs to:

1. Create a [GitHub OAuth token][7] with 'repo' permissions.
1. Run `export GITHUB_OAUTH_TOKEN=<token from above>` to set the environment variable.
1. Download and unzip [SubGit][6] in the current directory.
1. Edit line 5 of `util.sh` with their own GitHub username and line 6 with `apertium`.
1. Freeze the SVN repository.
1. Run `./import-modules.sh`.
1. Run `./create-metarepos.sh`.
1. Pin meta repositories.

## Maintenance

- [`sync.py`][5] recieves events from GitHub web hooks.
- Any updates to repositories with the appropriate tags will be pushed to the appropriate meta-repository.
- New repositories with a valid topic will be added to the appropriate meta-repository.
- Deleted repositories with a valid topic will be deleted from the appropriate meta-repository.

Usage:

    usage: sync.py [-h] [--verbose] [--dir DIR]
                  [--repo {apertium-languages,apertium-nursery,apertium-staging,apertium-incubator,apertium-all,apertium-trunk,apertium-tools}]
                  [--port PORT] [--token TOKEN] [--sync-interval SYNC_INTERVAL]
                  {sync,startserver}

    Sync Apertium meta repositories.

    positional arguments:
      {sync,startserver}    use "startserver" to start the server and "sync --repo
                            [name]" to force a meta-repo sync

    optional arguments:
      -h, --help            show this help message and exit
      --verbose, -v         add verbosity (maximum -vv)
      --dir DIR, -d DIR     directory to clone meta repos
      --repo {apertium-languages,apertium-nursery,apertium-staging,apertium-incubator,apertium-all,apertium-trunk,apertium-tools}, -r {apertium-languages,apertium-nursery,apertium-staging,apertium-incubator,apertium-all,apertium-trunk,apertium-tools}
                            meta-repo to sync (default: all)
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

## Git Tips

- Remember, GitHub has a [Subversion bridge][8] that makes it possible to use SVN to work with any of the non meta repositories.
- Kernel.org's [Git for SVN users cheatsheet][9].
- Meta repositories
  - Don't push updated submodules to a meta repository, let `sync.py` handle it.
  - To checkout a meta repository, use `git clone --recursive -j8 [url]`.
  - To pull (update) a meta repository, use `git pull --recurse-submodules`.
    Never use `git submodule update`, you will get conflicts with the sync script's pushes.
  - To commit changes to all submodules within a meta repository, use `git submodule foreach 'git commit -m "my message"'`.
    Add the `-a` flag to add unstaged files. If some submodules are dirty, use `git commit -m "my message" || true`.
  - To push changes to submodules within a meta repository, use `git submodule foreach git push`.
- Use Git [alias][10] for any oft used commands.

[1]: https://help.github.com/articles/permission-levels-for-an-organization/
[2]: https://github.com/orgs/apertium/
[3]: https://help.github.com/articles/repository-permission-levels-for-an-organization/
[4]: https://github.com/blog/2191-pin-repositories-to-your-github-profile
[5]: https://github.com/sushain97/apertium-on-github/blob/master/sync.py
[6]: https://subgit.com/
[7]: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/
[8]: https://help.github.com/articles/support-for-subversion-clients/
[9]: https://git.wiki.kernel.org/images-git/7/78/Git-svn-cheatsheet.pdf
[10]: https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases
[11]: https://developer.github.com/v3/repos/collaborators/#rate-limits
