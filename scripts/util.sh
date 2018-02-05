#!/bin/sh

set -x -u -e

USER='sushain97'
ORG='mock-apertium'
CWD=${BASH_SOURCE[0]%/*}

delete_repo () {
    curl -X DELETE https://api.github.com/repos/$ORG/$1 -u $USER:$GITHUB_OAUTH_TOKEN
}

create_repo () {
    curl -s -S -X POST https://api.github.com/orgs/$ORG/repos \
            -u $USER:$GITHUB_OAUTH_TOKEN \
            -d "{\"name\":\"$1\"}"
}

set_repo_topics () {
    curl -s -S -X PUT https://api.github.com/repos/$ORG/$1/topics \
        -u $USER:$GITHUB_OAUTH_TOKEN \
        -d "{\"names\":$2}" \
        -H "Accept:application/vnd.github.mercy-preview+json"
}

import_repo () {
    $CWD/../subgit-3.2.6/bin/subgit configure \
        --layout directory \
        --svn-url $1
    cp $CWD/../authors.txt $2.git/subgit/authors.txt
    $CWD/../subgit-3.2.6/bin/subgit install $2.git
}
