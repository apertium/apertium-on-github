#!/bin/sh

source util.sh

languages=( $(svn ls https://svn.code.sf.net/p/apertium/svn/languages | grep -E "^apertium-$LANG_RE/$" | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    import_create_and_push_repo "https://svn.code.sf.net/p/apertium/svn/languages/$lang/" $lang '["languages"]'
done

modules=( $(svn ls https://svn.code.sf.net/p/apertium/svn/incubator | grep -E "^apertium-$LANG_RE(-$LANG_RE)?/$" | cut -d '/' -f 1) )
for module in "${modules[@]}"
do
    import_create_and_push_repo "https://svn.code.sf.net/p/apertium/svn/incubator/$module/" $module '["apertium-incubator"]'
done

PAIR_LOCATIONS=(nursery incubator trunk)
for pair_location in "${PAIR_LOCATIONS[@]}"
do
    pairs=( $(svn ls https://svn.code.sf.net/p/apertium/svn/${pair_location} | grep -E "^apertium-$LANG_RE-$LANG_RE/$" | cut -d '/' -f 1) )
    for pair in "${pairs[@]}"; do
        import_create_and_push_repo "https://svn.code.sf.net/p/apertium/svn/${pair_location}/$pair/" $pair "[\"apertium-${pair_location}\"]"
    done
done
