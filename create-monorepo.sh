#!/bin/sh

ORG='mock-apertium'
USER='sushain97'
MONOREPO='languages'

git clone git@github.com:$ORG/$MONOREPO.git
cd $MONOREPO/

languages=( afr ara arg ast ava bak bel ben bre bul cat ces chv cos crh cym dan deu ell eng eus fao fra gla glg glv hbs heb hin hye ind isl ita kaa kaz kir kmr kum ltz lvs mar mkd mlt nld nno nob nog oci pol por quz qve ron rus sah san scn slv spa sqi srd swe tat tet tuk tur tyv ukr urd uzb zho zlm )
for lang in "${languages[@]}"
do
    git submodule add git@github.com:$ORG/apertium-$lang.git
done
git commit -m "Update submodules"
git push
