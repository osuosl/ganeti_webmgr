#!/bin/bash

PARENT_BRANCH='develop'

DOC_PATTERNS_LIST=( 'docs/' 'README' 'CHANGELOG' )

CHANGED_FILES=`git rev-list HEAD ^$PARENT_BRANCH | xargs git show --pretty="format:" --name-only`

for PATTERN in "${DOC_PATTERNS_LIST[@]}"; do
	echo next pattern
	echo $PATTERN
	if [[ $CHANGED_FILES =~ $PATTERN ]]; then
		exit 0
	fi
done

exit 1
