#!/bin/bash
# Add ssh keys from a Ganeti Web Manager instance to a VM

set -e

if [ -z "${AUTHORIZED_KEYS}" ] ; then
    echo "Missing authorized keys location"
    exit 1
fi

if [ -z "${GWM_SSHKEYS}" -o ! -x "${GWM_SSHKEYS}" ] ; then
    echo "Missing Ganeti Web Manager sshkeys.py"
    exit 1
fi

if [ -z "${GWM_API_KEY}" ] ; then
    echo "GWM_API_KEY empty"
    exit 1
fi

if [ -z "${GWM_HOST}" ] ; then
    echo "GWM_HOST empty"
    exit 1
fi

cluster_arg=""
if [ ! -z "${GWM_SLUG}" ] ; then
    cluster_arg="-c ${GWM_SLUG}"
fi

instance_arg=""
if [ ! -z "${INSTANCE_NAME}" ] && [ -z "${GWM_SLUG}" ]; then
    echo "Error, INSTANCE_NAME set, but GWM_SLUG not set."
    exit 1
elif [ ! -z "${INSTANCE_NAME}" ] && [ ! -z "${GWM_SLUG}" ]; then
    instance_arg="-i ${INSTANCE_NAME}"
fi

# Quotes are important! They keep spaces
end_args="${cluster_arg} ${instance_arg}"

args="${GWM_API_KEY} ${GWM_HOST} ${end_args}"

TMPFILE='mktemp' || exit 1
# This line is the entire sshkeys.py command with args
${GWM_SSHKEYS} $args > $TMPFILE

if [ $? -eq 0 ] # Did the command work?
then # Success
    cat $TMPFILE > ${AUTHORIZED_KEYS}
    rm -rf $TMPFILE
    exit 0
else # Fail
    echo "An error occured. Error: \n"
    cat $TMPFILE
    rm -rf $TMPFILE
    exit 1
fi

exit 0
