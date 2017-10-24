#!/bin/sh

ORG='mock-apertium'
USER='sushain97'

languages=( $(svn ls https://svn.code.sf.net/p/apertium/svn/languages | grep / | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    # delete existing stuff
    # rm -rf $lang.git/
    # curl -X DELETE https://api.github.com/repos/$ORG/$lang -u $USER:$GITHUB_OAUTH_TOKEN

    # do the import
    ../subgit-3.2.6/bin/subgit configure \
        --layout directory \
        --svn-url https://svn.code.sf.net/p/apertium/svn/languages/$lang/
    cp ../authors.txt $lang.git/subgit/authors.txt
    ../subgit-3.2.6/bin/subgit install $lang.git

    # setup the new repo
    curl -s -S -X POST https://api.github.com/orgs/$ORG/repos \
        -u $USER:$GITHUB_OAUTH_TOKEN \
        -d "{\"name\":\"$lang\"}"
    cd $lang.git/
    git remote add origin git@github.com:$ORG/$lang.git
    git push origin --force --all
    curl -s -S -X PUT https://api.github.com/repos/$ORG/$lang/topics \
        -u $USER:$GITHUB_OAUTH_TOKEN \
        -d '{"names":["languages"]}' \
        -H "Accept:application/vnd.github.mercy-preview+json"

    # clean up
    cd ..
    rm -rf $lang.git/
done
