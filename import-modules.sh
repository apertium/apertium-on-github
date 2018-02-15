#!/bin/sh

source util.sh

languages=( $(svn ls $SVN_ROOT/languages | grep -E "^apertium-$LANG_RE/$" | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    import_create_and_push_repo "$SVN_ROOT/languages/$lang/" $lang '["apertium-languages"]'
done

modules=( $(svn ls $SVN_ROOT/incubator | grep -E "^apertium-$LANG_RE(-$LANG_RE)?/$" | cut -d '/' -f 1) )
for module in "${modules[@]}"
do
    import_create_and_push_repo "$SVN_ROOT/incubator/$module/" $module '["apertium-incubator"]'
done

PAIR_LOCATIONS=(nursery staging trunk)
for pair_location in "${PAIR_LOCATIONS[@]}"
do
    pairs=( $(svn ls $SVN_ROOT/${pair_location} | grep -E "^apertium-$LANG_RE-$LANG_RE/$" | cut -d '/' -f 1) )
    for pair in "${pairs[@]}"; do
        import_create_and_push_repo "$SVN_ROOT/${pair_location}/$pair/" $pair "[\"apertium-${pair_location}\"]"
    done
done
