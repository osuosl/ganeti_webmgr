# coding: utf-8

# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

import binascii
from datetime import datetime, timedelta
from hashlib import sha1
import random
import re
import string
import sys
import time

from django.conf import settings

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites import models as sites_app
from django.contrib.sites.management import create_default_site
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.db.models import BooleanField, Q, Sum
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, post_syncdb
from django.db.utils import DatabaseError
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from django_fields.fields import PickleField

from utils.logs import register_log_actions

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from object_permissions.registration import register

from muddle_users import signals as muddle_user_signals

from ganeti_web import constants, management, permissions
from utils.fields import (PatchedEncryptedCharField, PreciseDateTimeField,
                          SumIf)
from utils import client
from utils.client import GanetiApiError, REPLACE_DISK_AUTO

from south.signals import post_migrate

if settings.VNC_PROXY:
    from utils.vncdaemon.vapclient import request_forwarding, request_ssh


def generate_random_password(length=12):
    "Generate random sequence of specified length"
    return "".join(random.sample(string.letters + string.digits, length))

FINISHED_JOBS = 'success', 'unknown', 'error'

RAPI_CACHE = {}
RAPI_CACHE_HASHES = {}


def get_rapi(hash, cluster):
    """
    Retrieves the cached Ganeti RAPI client for a given hash.  The Hash is
    derived from the connection credentials required for a cluster.  If the
    client is not yet cached, it will be created and added.

    If a hash does not correspond to any cluster then Cluster.DoesNotExist will
    be raised.

    @param cluster - either a cluster object, or ID of object.  This is used
    for resolving the cluster if the client is not already found.  The id is
    used rather than the hash, because the hash is mutable.

    @return a Ganeti RAPI client.
    """
    if hash in RAPI_CACHE:
        return RAPI_CACHE[hash]

    # always look up the instance, even if we were given a Cluster instance
    # it ensures we are retrieving the latest credentials.  This helps avoid
    # stale credentials.  Retrieve only the values because we don't actually
    # need another Cluster instance here.
    if isinstance(cluster, (Cluster,)):
        cluster = cluster.id
    (credentials,) = Cluster.objects.filter(id=cluster) \
        .values_list('hash', 'hostname', 'port', 'username', 'password')
    hash, host, port, user, password = credentials
    user = user or None
    # decrypt password
    # XXX django-fields only stores str, convert to None if needed
    password = Cluster.decrypt_password(password) if password else None
    password = None if password in ('None', '') else password

    # now that we know hash is fresh, check cache again. The original hash
    # could have been stale. This avoids constructing a new RAPI that already
    # exists.
    if hash in RAPI_CACHE:
        return RAPI_CACHE[hash]

    # delete any old version of the client that was cached.
    if cluster in RAPI_CACHE_HASHES:
        del RAPI_CACHE[RAPI_CACHE_HASHES[cluster]]

    # Set connect timeout in settings.py so that you do not learn patience.
    rapi = client.GanetiRapiClient(host, port, user, password,
                                   timeout=settings.RAPI_CONNECT_TIMEOUT)
    RAPI_CACHE[hash] = rapi
    RAPI_CACHE_HASHES[cluster] = hash
    return rapi


def clear_rapi_cache():
    """
    clears the rapi cache
    """
    RAPI_CACHE.clear()
    RAPI_CACHE_HASHES.clear()


ssh_public_key_re = re.compile(
    r'^ssh-(rsa|dsa|dss) [A-Z0-9+/=]+ .+$', re.IGNORECASE)
ssh_public_key_error = _("Enter a valid RSA or DSA SSH key.")
validate_sshkey = RegexValidator(ssh_public_key_re, ssh_public_key_error,
                                 "invalid")


def create_profile(sender, instance, **kwargs):
    """
    Create a profile object whenever a new user is created, also keeps the
    profile name synchronized with the username
    """
    try:
        profile, new = Profile.objects.get_or_create(user=instance)
        if profile.name != instance.username:
            profile.name = instance.username
            profile.save()
    except DatabaseError:
        # XXX - since we're using south to track migrations the Profile table
        # won't be available the first time syncdb is run.  Catch the error
        # here and let the south migration handle it.
        pass


def update_cluster_hash(sender, instance, **kwargs):
    """
    Updates the Cluster hash for all of it's VirtualMachines, Nodes, and Jobs
    """
    instance.virtual_machines.all().update(cluster_hash=instance.hash)
    instance.jobs.all().update(cluster_hash=instance.hash)
    instance.nodes.all().update(cluster_hash=instance.hash)


def update_organization(sender, instance, **kwargs):
    """
    Creates a Organizations whenever a contrib.auth.models.Group is created
    """
    org, new = Organization.objects.get_or_create(group=instance)
    org.name = instance.name
    org.save()

post_save.connect(create_profile, sender=User)
post_save.connect(update_cluster_hash, sender=Cluster)
post_save.connect(update_organization, sender=Group)

# Disconnect create_default_site from django.contrib.sites so that
#  the useless table for sites is not created. This will be
#  reconnected for other apps to use in update_sites_module.
post_syncdb.disconnect(create_default_site, sender=sites_app)
post_syncdb.connect(management.update_sites_module, sender=sites_app,
                    dispatch_uid="ganeti.management.update_sites_module")


def regenerate_cu_children(sender, **kwargs):
    """
    Resets may destroy Profiles and/or Organizations. We need to regenerate
    them.
    """

    # So. What are we actually doing here?
    # Whenever a User or Group is saved, the associated Profile or
    # Organization is also updated. This means that, if a Profile for a User
    # is absent, it will be created.
    # More importantly, *why* might a Profile be missing? Simple. Resets of
    # the ganeti app destroy them. This shouldn't happen in production, and
    # only occasionally in development, but it's good to explicitly handle
    # this particular case so that missing Profiles not resulting from a reset
    # are easier to diagnose.
    try:
        for user in User.objects.filter(profile__isnull=True):
            user.save()
        for group in Group.objects.filter(organization__isnull=True):
            group.save()
    except DatabaseError:
        # XXX - since we're using south to track migrations the Profile table
        # won't be available the first time syncdb is run.  Catch the error
        # here and let the south migration handle it.
        pass

post_syncdb.connect(regenerate_cu_children)


def log_group_create(sender, editor, **kwargs):
    """ log group creation signal """
    log_action('CREATE', editor, sender)


def log_group_edit(sender, editor, **kwargs):
    """ log group edit signal """
    log_action('EDIT', editor, sender)


muddle_user_signals.view_group_created.connect(log_group_create)
muddle_user_signals.view_group_edited.connect(log_group_edit)


def refresh_objects(sender, **kwargs):
    """
    This was originally the code in the 0009
    and then 0010 'force_object_refresh' migration

    Force a refresh of all Cluster, Nodes, and VirtualMachines, and
    import any new Nodes.
    """

    if kwargs.get('app', False) and kwargs['app'] == 'ganeti_web':
        Cluster.objects.all().update(mtime=None)
        Node.objects.all().update(mtime=None)
        VirtualMachine.objects.all().update(mtime=None)

        write = sys.stdout.write
        flush = sys.stdout.flush

        def wf(str, newline=False):
            if newline:
                write('\n')
            write(str)
            flush()

        wf('- Refresh Cached Cluster Objects')
        wf(' > Synchronizing Cluster Nodes ', True)
        flush()
        for cluster in Cluster.objects.all().iterator():
            try:
                cluster.sync_nodes()
                wf('.')
            except GanetiApiError:
                wf('E')

        wf(' > Refreshing Node Caches ', True)
        for node in Node.objects.all().iterator():
            try:
                wf('.')
            except GanetiApiError:
                wf('E')

        wf(' > Refreshing Instance Caches ', True)
        for instance in VirtualMachine.objects.all().iterator():
            try:
                wf('.')
            except GanetiApiError:
                wf('E')
        wf('\n')


# Set this as post_migrate hook.
post_migrate.connect(refresh_objects)

# Register permissions on our models.
# These are part of the DB schema and should not be changed without serious
# forethought.
# You *must* syncdb after you change these.
register(permissions.CLUSTER_PARAMS, Cluster, 'ganeti_web')
register(permissions.VIRTUAL_MACHINE_PARAMS, VirtualMachine, 'ganeti_web')


# register log actions
register_log_actions()
