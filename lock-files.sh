#!/bin/bash

source util.sh

message='Apertium has migrated to Git/GitHub. See repositories at https://apertium.github.io/apertium-on-github/source-browser.html. DO NOT USE SourceForge/SVN. This repo will be deleted.'
svn list --recursive $SVN_ROOT | \
    awk '!/\/$/' | \
    awk -v root="$SVN_ROOT" '{ print root "/"$0"" }' |
    xargs -n 25 -d '\n' svn lock --force --message "$message"
