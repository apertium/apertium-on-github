#!/bin/sh
source "${BASH_SOURCE[0]%/*}/util.sh"

pairs=( $(svn ls https://svn.code.sf.net/p/apertium/svn/staging | grep / | cut -d '/' -f 1) )
for pair in "${pairs[@]}"
do
    # delete existing stuff
    # rm -rf $pair.git/
    # delete $pair

    import_repo "https://svn.code.sf.net/p/apertium/svn/staging/$pair/" $pair

    # setup the new repo
    create_repo $pair
    cd $pair.git/
    git remote add origin git@github.com:$ORG/$pair.git
    git push origin --force --all
    set_repo_topics $pair '["apertium-staging"]'

    # clean up
    cd ..
    rm -rf $pair.git/
done
