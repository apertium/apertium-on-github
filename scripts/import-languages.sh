#!/bin/sh
source "${BASH_SOURCE[0]%/*}/util.sh"

languages=( $(svn ls https://svn.code.sf.net/p/apertium/svn/languages | grep / | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    # rm -rf $lang.git/
    # delete_repo $lang
    import_create_and_push_repo "https://svn.code.sf.net/p/apertium/svn/languages/$lang/" $lang '["languages"]'
done
