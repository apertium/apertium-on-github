source "${BASH_SOURCE[0]%/*}/util.sh"

svn_url=$1
repo_name=$2
repo_topic=$3

import_repo $svn_url $repo_name
create_repo $repo_name
push_bare_repo $repo_name
set_repo_topics $repo_name "[\"$repo_topic\"]"
rm -rf $repo_name.git/
