#!/bin/sh
source util.sh

# setup the remainder
metarepos=(staging nursery incubator trunk languages tools)
for repo in "${metarepos[@]}"
do
    create_repo "apertium-$repo"
    set_repo_topics "apertium-$repo" '["apertium-all"]'
    init_repo "apertium-$repo"
    ./sync.py sync --repo "apertium-$repo"
done

# setup apertium-all
create_repo "apertium-all"
init_repo "apertium-all"
./sync.py sync --repo apertium-all
