#!/bin/sh
source "${BASH_SOURCE[0]%/*}/util.sh"

languages=( $(svn ls https://svn.code.sf.net/p/apertium/svn/languages | grep / | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    # delete existing stuff
    # rm -rf $lang.git/
    # delete $lang

    import_repo "https://svn.code.sf.net/p/apertium/svn/languages/$lang/" $lang

    # setup the new repo
    create_repo $lang
    push_bare_repo $lang
    set_repo_topics $lang '["languages"]'

    # clean up
    rm -rf $lang.git/
done
