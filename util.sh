#!/bin/bash

set -x -u -e -a
export SHELLOPTS

MAX_PROCS=8
SUBGIT=./subgit-3.2.6/bin/subgit
SVN_ROOT='https://svn.code.sf.net/p/apertium/svn'
GITHUB_API='https://api.github.com'
USER='sushain97'
ORG='apertium'
LANG_RE='\w{2,3}(_\w+)?'

delete_repo () {
    curl -X DELETE "$GITHUB_API/repos/$ORG/$1" -u "$USER:$GITHUB_OAUTH_TOKEN"
}

create_repo () {
    curl -s -S -X POST $GITHUB_API/orgs/$ORG/repos \
            -u "$USER:$GITHUB_OAUTH_TOKEN" \
            -d "{\"name\":\"$1\"}"
}

init_repo () {
    git clone "git@github.com:$ORG/$1.git"
    (
        cd "$1"
        echo "# $1" > README.md
        git add README.md
        git diff-index --quiet HEAD || git commit -m "Initial commit"
        git push
    )
    rm -rf "$1"
}

set_repo_topics () {
    curl -s -S -X PUT "$GITHUB_API/repos/$ORG/$1/topics" \
        -u "$USER:$GITHUB_OAUTH_TOKEN" \
        -d "{\"names\":$2}" \
        -H "Accept:application/vnd.github.mercy-preview+json"
}

import_repo () {
    $SUBGIT configure \
        --layout auto \
        --svn-url $SVN_ROOT \
        --trunk "$1" \
        "$2.git"
    cp ./svn-authors.txt "$2.git/subgit/authors.txt"
    $SUBGIT import "$2.git"
}

push_bare_repo () {
    (
        cd "$1.git/"
        git remote add origin "git@github.com:$ORG/$1.git"
        git push origin --force --all
        git push origin --force --tags
        git push origin --force refs/notes/*
    )
}

exists_repo () {
    curl -s -S "$GITHUB_API/repos/$ORG/$1" \
        -u "$USER:$GITHUB_OAUTH_TOKEN" \
        -w "%{http_code}" \
        -o /dev/null
}

import_create_and_push_repo () {
    if [[ $( exists_repo "$2" ) == '200' ]]
    then
        echo "$2 already exists in $ORG";
    else
        import_repo "$1" "$2"
        create_repo "$2"
        push_bare_repo "$2"
        set_repo_topics "$2" "$3"
        rm -rf "$2.git/"
    fi
}
