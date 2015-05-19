#!/bin/bash


# Hello future developers! You are probably wondering whose stupid idea it was
# to write this script, you just want to get your tests to pass and your code
# to merge. An excellent sentiment! However, consider the state of the project
# as a whole. When this was written, the docs and tests of GWM were out of date
# Many configuration options were undocumented. GWM did strange things
# everywhere and we couldn't figure out why. We decided that new features and
# new PRs should require docs. You will probably be at the lab for a relatively
# short time, so please be considerate of those who come after you.



# Travis CI runs some commands which look kind of like this. We rely on the
# repo having a merge commit as the most recent commit.
# If Travis changes the way it starts up this script might break. Don't
# despair! You'll probably only need to change PARENT_1 and PARENT_2 below,
# everything else should work fine.
#   $ git clone --depth=50 git://github.com/osuosl/ganeti_webmgr.git osuosl/ganeti_webmgr
#   $ cd osuosl/ganeti_webmgr
#   $ git fetch origin +refs/pull/36/merge:
#   $ git checkout -qf FETCH_HEAD

PREV_COMMIT=`git rev-list --parents HEAD -n 1`
if [[ `echo $PREV_COMMIT | wc -w`  -lt 3 ]]; then
	echo "This is a Push, not a PR. Not checking for docs."
	exit 0
fi

# The rev-list command with our arguments lists the current commit, and since
# this is a merge commit (since it's on Travis) the fist hash is the current
# commit, the second is the first parent, and the third is the second parent.
# We get the right hashes with cut.
PARENT_1=`echo $PREV_COMMIT | cut -f2 -d' '`
PARENT_2=`echo $PREV_COMMIT | cut -f3 -d' '`

# This is a list of files or directories which are documentation.
DOC_MATCHES=( 'docs/' 'README' 'CHANGELOG' )

# This is the list of files which changed since the branch diverged.
# rev-list shows the revisions which appear between the first and second
# parents of the branch. We then run get show on each revision to list the
# files which changed.
CHANGED_FILES=`git rev-list $PARENT_2 ^$PARENT_1 | xargs git show --pretty="format:" --name-only`

# Now, for each file/directory in the list of documentation mateches, check to
# to see if it is in the list of changed files. If it matches, we know that a
# a file which contains documentation changed. Humans now need to look at the
# changes and check that the changes are sufficient, correct, and sensible.
for PATTERN in "${DOC_MATCHES[@]}"; do
	if [[ $CHANGED_FILES =~ $PATTERN ]]; then
		echo "Yay, you wrote some docs! Here's a gold star: 🌟 "
		exit 0
	fi
done

NAME_OF_THIS_SCRIPT=`basename $0`

# If no matches were found, tell the human why this test failed and what they
# can do about it.
echo "No docs were included since you began this branch.
You should do one of three things:
1. Write some docs.
2. Justify why you think this change doesn't require docs in the PR. You're
   smarter than the robots, but the robots want you to think about what you're
   doing.
3. If you *did* write docs, you should tell the robots where you put the docs.
   Edit the DOC_MATCHES variable in the $NAME_OF_THIS_SCRIPT file in the repo."

# Fail the test because no matches were found.
exit 1
