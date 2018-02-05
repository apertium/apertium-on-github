#!/bin/sh

CWD=${BASH_SOURCE[0]%/*}

source "$CWD/util.sh"
$CWD/import-languages.sh
$CWD/import-staging.sh
$CWD/create-monorepos.sh
