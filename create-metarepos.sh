#!/bin/sh
source util.sh
set +u

create_metarepo () {
    create_repo "apertium-$1"
    set_repo_topics "apertium-$1" '["apertium-all"]'
    init_repo "apertium-$1"
    ./sync.py sync --repo "apertium-$1"
}

metarepos=(staging nursery incubator trunk languages tools)
printf "%s\n" "${metarepos[@]}" | xargs -n 1 -I {} bash -c 'create_metarepo "{}"'

# setup apertium-all
create_repo "apertium-all"
init_repo "apertium-all"
./sync.py sync --repo apertium-all
