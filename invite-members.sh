#!/bin/sh

source util.sh

invite () {
    curl -s -S -X POST $GITHUB_API/orgs/$ORG/invitations \
            -u $USER:$GITHUB_OAUTH_TOKEN \
            -d "{\"email\":\"$1\", \"role\": \"direct_member\"}" \
            -H "Accept:application/vnd.github.dazzler-preview+json"
}

sed 's/^.*<\(.*\)>/\1/' svn-authors.txt | grep -v '@users.sourceforge.net' | xargs -n 1 -I {} bash -c 'invite "{}"'
