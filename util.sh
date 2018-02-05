#!/bin/sh

set -x -u -e

USER='sushain97'
ORG='mock-apertium'
LANG_RE='\w{2,3}(_\w{2,3})?'

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

push_bare_repo () {
    (
        cd $1.git/
        git remote add origin git@github.com:$ORG/$1.git
        git push origin --force --all
    )
}

import_create_and_push_repo () {
    import_repo $1 $2
    create_repo $2
    push_bare_repo $2
    set_repo_topics $2 $3
    rm -rf $2.git/
}
