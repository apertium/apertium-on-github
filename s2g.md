# s2g - svn-to-git with mixed histories

## The Tools
- `s2g-map.php /path/to/folder REV` creates a list of revisions and what path the folder had in that revision. REV defaults to HEAD but can be any valid revision number.
- `s2g-import.php REVFILE AUTHORFILE` takes a file with a list of revision to path mappings and imports those to a git repository.
- `s2g-am.php PATCHFILE` sets environment variables and runs `git am` to simulate author == committer. Used for transferring post-svn history from existing git repo.

## Real-World Example: apertium-spa-arg
First map current latest version:<br>
`./s2g-map.php /trunk/apertium-spa-arg | tee map`

Then add to the map the revisions from the copied-from folders:<br>
`./s2g-map.php /trunk/apertium-es-an | tee -a map`

This says the oldest revision is 31754, but the log for [31754](https://apertium.projectjj.com/trac/changeset/31754/) shows that's a newly created empty folder, and the subsequent revision [31755](https://apertium.projectjj.com/trac/changeset/31755/) copies in a bunch of files from `/incubator/apertium-es-an`.

Edit `map` to remove 31754, or the import will happily make a revision where all files vanished.

Next up, figure out what's the oldest revision `/incubator/apertium-es-an` exists in. This requires some manual digging through the [log from 31754 backwards](https://apertium.projectjj.com/trac/log/?rev=31754), and we can determine [31740](https://apertium.projectjj.com/trac/changeset/31740/) is what deletes the folder, so we want 31739:<br>
`./s2g-map.php /trunk/apertium-es-an 31739 | tee -a map`

Splice all those revisions to one git repo:<br>
`./s2g-import.php map svn-authors.txt`

...except that throws an error because [10206](https://apertium.projectjj.com/trac/changeset/10206/) moved the parent `/incubator` folder from `/branches/incubator`, which `s2g-map.php` does not handle.

Wipe `/tmp/s2g-*` and edit `map` to change `10198 /incubator/apertium-es-an` to `10198 /branches/incubator/apertium-es-an` and rerun:<br>
`./s2g-import.php map svn-authors.txt`

We now have a usable git repo in `/tmp/s2g-*/git` and we need to merge back the changes made in git since the original svn conversion:<br>
`cd /tmp/s2g-*`<br>
`git clone git@github.com:apertium/apertium-spa-arg.git`<br>
`cd apertium-spa-arg`

Determine when the first conversion was done, and export those changesets:<br>
`git format-patch -o ../ -k c160a824^..HEAD`<br>
`cd ../git`

Import the changesets one-by-one and fix errors if they happen:<br>
`~apertium/apertium-on-github/s2g-am.php ../0001-*.patch`<br>
...<br>
`~apertium/apertium-on-github/s2g-am.php ../0009-*.patch`

When amending, it can be useful to recreate the changes but keep the old timestamp, plus ensure author == committer. This is done via e.g.:<br>
`export 'GIT_COMMITTER_DATE=Sat, 17 Mar 2018 02:02:24 -0500' 'GIT_COMMITTER_NAME=Sushain Cherivirala' 'GIT_COMMITTER_EMAIL=sushain@skc.name'`<br>
`git commit --author 'Sushain Cherivirala <sushain@skc.name>' --date 'Sat, 17 Mar 2018 02:02:24 -0500' -m 'Update/add .gitignore and .gitattributes'`

Ensure all looks good, add remote and force-push changes:<br>
`git remote add origin git@github.com:apertium/apertium-spa-arg.git`<br>
`git push origin master -f`
