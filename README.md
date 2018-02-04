Apertium on Github
==================

Proposal
--------
See [PMC_proposals/Move_Apertium_to_Github](http://wiki.apertium.org/wiki/PMC_proposals/Move_Apertium_to_Github).

Structure
---------

- Each package will have its own repository.
- "Meta repositories" will contain only submodules.
    - `apertium-all` will contain `apertium-core`, `apertium-tools`, `apertium-staging`, `apertium-incubator`, `apertium-nursery`, `apertium-trunk`.
    - `apertium-core` will contain the core.
    - `apertium-tools` will contain tools (repos marked with topic `tools`).
    - `apertium-staging` will contain staging language pairs (repos marked with topic `staging`).
    - `apertium-nursery` will contain nursery language pairs (repos marked with topic `nursery`).
    - `apertium-incubator` will contain staging language modules/pairs (repos marked with topic `incubator`).
    - `apertium-trunk` will contain trunk language modules/pairs(repos marked with topic `trunk`).
- Meta repositories will be kept up-to-date by scripts (described below).
- SVN external properties will be used to maintain some backwards compatability.

**N.B.** The topics (a.k.a. tags) are integral.

Transition
----------

- TODO: import document and finish scripts
- TODO: svn propset script
- TODO: org setup (including pinning)

Maintenance
-----------

- The The TODO script recieves events from GitHub web hooks.
- Any updates to repositories with the appropriate tags will be pushed to the appropriate meta-repository.
- New repositories with a valid topic will be added to the  meta-repository.
- Deleted repositories with a valid topic will be deleted from the appropriate meta-repository.

TODO: maybe the script should just nuke and restart each time? could get pretty tricky...

Interface
---------

- TODO: document and finish web interface
- TODO: mention repo pinning


Helpful Git Commands
--------------------

- Remember, [`git svn`](https://git-scm.com/book/en/v1/Git-and-Other-Systems-Git-and-Subversion) is always an option and offers an bona fide SVN experience.
- Kernel.org's [Git for SVN users cheatsheet](https://git.wiki.kernel.org/images-git/7/78/Git-svn-cheatsheet.pdf).
- TODO: submodule commands