#!/bin/sh

ORG='mock-apertium'
USER='sushain97'

languages=( afr ara arg ast ava bak bel ben bre bul cat ces chv cos crh cym dan deu ell eng eus fao fra gla glg glv hbs heb hin hye ind isl ita kaa kaz kir kmr kum ltz lvs mar mkd mlt nld nno nob nog oci pol por quz qve ron rus sah san scn slv spa sqi srd swe tat tet tuk tur tyv ukr urd uzb zho zlm )

for lang in "${languages[@]}"
do
    # delete existing stuff
    # rm -rf apertium-$lang.git/
    # curl -X DELETE https://api.github.com/repos/$ORG/apertium-$lang -u $USER:$GITHUB_OAUTH_TOKEN

    # do the import
    ./subgit-3.2.6/bin/subgit configure \
        --layout directory \
        --svn-url https://svn.code.sf.net/p/apertium/svn/languages/apertium-$lang/
    cp authors.txt apertium-$lang.git/subgit/authors.txt
    ./subgit-3.2.6/bin/subgit install apertium-$lang.git

    # setup the new repo
    curl -s -S -X POST https://api.github.com/orgs/$ORG/repos \
        -u $USER:$GITHUB_OAUTH_TOKEN \
        -d "{\"name\":\"apertium-$lang\"}"
    cd apertium-$lang.git/
    git remote add origin git@github.com:$ORG/apertium-$lang.git
    git push origin --force --all
    curl -s -S -X PUT https://api.github.com/repos/$ORG/apertium-$lang/topics \
        -u $USER:$GITHUB_OAUTH_TOKEN \
        -d '{"names":["languages"]}' \
        -H "Accept:application/vnd.github.mercy-preview+json"

    # clean up
    cd ..
    rm -rf apertium-$lang.git/
done