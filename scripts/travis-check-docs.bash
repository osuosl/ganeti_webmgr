#!/bin/bash

PARENT_BRANCH='develop'

DOC_PATTERNS_LIST=( 'docs/' 'README' 'CHANGELOG' )

# The parent branch may not be present on Travis. Fetch it so we can compare
# our differences with git rev-list
git fetch origin $PARENT_BRANCH

CHANGED_FILES=`git rev-list HEAD ^$PARENT_BRANCH | xargs git show --pretty="format:" --name-only`

for PATTERN in "${DOC_PATTERNS_LIST[@]}"; do
	if [[ $CHANGED_FILES =~ $PATTERN ]]; then
		echo "Yay, you wrote some docs! Here's a gold star: 🌟 "
		exit 0
	fi
done

echo "No docs were included since you branched off $PARENT_BRANCH. That's okay,
but you should justify why you don't need docs in the PR."

exit 1
