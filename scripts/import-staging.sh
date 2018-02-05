#!/bin/sh
source "${BASH_SOURCE[0]%/*}/util.sh"

pairs=( $(svn ls https://svn.code.sf.net/p/apertium/svn/staging | grep / | cut -d '/' -f 1) )
for pair in "${pairs[@]}"
do
    # rm -rf $pair.git/
    # delete_repo $pair
    import_create_and_push_repo "https://svn.code.sf.net/p/apertium/svn/staging/$pair/" $pair '["apertium-staging"]'
done
