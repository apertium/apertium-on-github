#!/bin/sh
source "${BASH_SOURCE[0]%/*}/util.sh"

# setup the remainder
METAREPOS=(apertium-staging)
for repo in "${METAREPOS[@]}"
do
    create_repo $repo
    set_repo_topics $repo '["apertium-all"]'
    ./sync.py sync --repo $repo
done

# setup apertium-all
create_repo "apertium-all"
./sync.py sync --repo apertium-all
