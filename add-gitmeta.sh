#!/bin/bash

source util.sh

GIT_ATTRIBUTES="*.dix linguist-language=XML linguist-detectable=true
*.lrx linguist-language=XML linguist-detectable=true
*.lsx linguist-language=XML linguist-detectable=true
*.tsx linguist-language=XML linguist-detectable=true
*.t[[:digit:]]x linguist-language=XML linguist-detectable=true"

GIT_IGNORE="/*.bin
/*.gz
/*.m4
/*.pc
/INSTALL
/Makefile
/Makefile.in
/ap_include.am
/autom4te.cache
/config.log
/config.status
/configure
/install-sh
/missing
/modes
/*.mode
/.deps
/config.in
/config"

# we could check out the meta-repos and do a git submodule foreach but that
# requires a much better internet connection than the one I have access to now

META_REPOS=(incubator languages nursery staging trunk)
for meta_repo in "${META_REPOS[@]}"
do
    repos=( $(svn cat "$GITHUB_ROOT/apertium-${meta_repo}.git/trunk/.gitmodules" | grep path | grep -oE "apertium-$LANG_RE(-$LANG_RE)?") )
    for repo in "${repos[@]}"
    do
        svn checkout "$GITHUB_ROOT/$repo.git/trunk" repo --depth empty
        (
            cd repo

            svn up .gitattributes
            if [ ! -f .gitattributes ]
            then
                echo "Creating gitattributes in $repo"
                echo "$GIT_ATTRIBUTES" > .gitattributes
                svn add .gitattributes
            else
                echo "Adding gitattributes to $repo"
                printf %s "$(< .gitattributes)" > .gitattributes # strip any existing trailing newline
                printf "\\n" >> .gitattributes # now, ensure there's a newline (exactly 1)
                echo "$GIT_ATTRIBUTES" >> .gitattributes # add our attributes
                awk '!seen[$0]++' .gitattributes > tmp_gitattributes && mv tmp_gitattributes .gitattributes # remove any duplicate lines
            fi

            svn up .gitignore
            if [ ! -f .gitignore ]  # we don't want to mess with any existing settings
            then
                echo "Creating gitignore in $repo"
                echo "$GIT_IGNORE" > .gitignore
                svn add .gitignore
            fi

            svn commit -m 'Update/add .gitignore and .gitattributes' .gitignore .gitattributes
        )
        rm -rf repo
    done
done
