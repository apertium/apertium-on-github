#!/bin/bash

source util.sh
set +u

languages=( $(svn ls $SVN_ROOT/languages | grep -E "^apertium-$LANG_RE/$" | cut -d '/' -f 1) )
printf "%s\n" "${languages[@]}" | xargs -n 1 -P $MAX_PROCS -I {} bash -c \
    'import_create_and_push_repo "languages/{}" {} "[\"apertium-languages\"]"'

modules=( $(svn ls $SVN_ROOT/incubator | grep -E "^apertium-$LANG_RE(-$LANG_RE)?/$" | cut -d '/' -f 1) )
printf "%s\n" "${modules[@]}" | xargs -n 1 -P $MAX_PROCS -I {} bash -c \
    'import_create_and_push_repo "incubator/{}" {} "[\"apertium-incubator\"]"'

PAIR_LOCATIONS=(nursery staging trunk)
for pair_location in "${PAIR_LOCATIONS[@]}"
do
    pairs=( $(svn ls $SVN_ROOT/${pair_location} | grep -E "^apertium-$LANG_RE-$LANG_RE/$" | cut -d '/' -f 1) )
    printf "%s\n" "${pairs[@]}" | xargs -n 1 -P $MAX_PROCS -I {} bash -c \
        'import_create_and_push_repo "${pair_location}/{}" {} "[\"apertium-${pair_location}\"]"'
done

import_create_and_push_repo "trunk/apertium" "apertium" "[\"apertium-core\"]"
import_create_and_push_repo "trunk/lttoolbox" "lttoolbox" "[\"apertium-core\"]"
import_create_and_push_repo "trunk/apertium-lex-tools" "apertium-lex-tools" "[\"apertium-core\"]"
import_create_and_push_repo "trunk/apertium-separable" "apertium-separable" "[\"apertium-core\"]"
