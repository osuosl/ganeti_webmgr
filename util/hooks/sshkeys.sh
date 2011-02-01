#!/bin/bash
# Add ssh keys from a Ganeti Web Manager instance to a VM

set -e

. common.sh

if [ -z "${TARGET}" -o ! -d "${TARGET}" ] ; then
    echo "Missing target directory"
    exit 1
fi

if [ -z "${GWM_SSHKEYS}" -o ! -x "${GWM_SSHKEYS}" ] ; then
    echo "Missing Ganeti Web Manager sshkeys.py"
    exit 1
fi

if [ -z "${GWM_HOST}" ] ; then
    echo "GWM_HOST empty"
    exit 1
fi

if [ -z "${GWM_SLUG}" ] ; then
    echo "GWM_SLUG empty"
    exit 1
fi

if [ -z "${GWM_API_KEY}" ] ; then
    echo "GWM_API_KEY empty"
    exit 1
fi

mkdir -p ${TARGET}/root/.ssh
${GWM_SSHKEYS} ${GWM_HOST} ${GWM_SLUG} \
    ${INSTANCE_NAME} ${GWM_API_KEY} > ${TARGET}/root/.ssh/authorized_keys

exit 0
