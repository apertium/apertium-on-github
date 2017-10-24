#!/bin/sh

ORG='mock-apertium'
MONOREPO='staging'

git clone git@github.com:$ORG/$MONOREPO.git
cd $MONOREPO/

languages=( $(svn ls https://svn.code.sf.net/p/apertium/svn/staging | grep / | cut -d '/' -f 1) )
for lang in "${languages[@]}"
do
    git submodule add git@github.com:$ORG/$lang.git
done
wget https://svn.code.sf.net/p/apertium/svn/staging/001-README -O README.md
git add .
git commit -m "Update submodules"
git push

cd ..
