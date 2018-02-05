#!/bin/sh
source util.sh

# setup the remainder
METAREPOS=(apertium-staging apertium-nursery apertium-incubator apertium-trunk apertium-languages)
for repo in "${METAREPOS[@]}"
do
    create_repo $repo
    set_repo_topics $repo '["apertium-all"]'
    ./sync.py sync --repo $repo
done

# setup apertium-all
create_repo "apertium-all"
./sync.py sync --repo apertium-all
