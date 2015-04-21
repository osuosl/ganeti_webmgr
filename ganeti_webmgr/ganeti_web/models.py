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

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites import models as sites_app
from django.contrib.sites.management import create_default_site
from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_syncdb
from django.db.utils import DatabaseError

from ganeti_webmgr.utils.logs import register_log_actions

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from object_permissions.registration import register

from ganeti_webmgr.muddle_users import signals as muddle_user_signals

from ganeti_webmgr.authentication.models import Organization
from ganeti_webmgr.clusters.models import Cluster
from ganeti_webmgr.nodes.models import Node
from ganeti_webmgr.virtualmachines.models import VirtualMachine
from ganeti_webmgr.utils.client import GanetiApiError

import permissions

from ganeti_webmgr.authentication.models import Profile

# XXX: am I wrong or is it not used anywhere?
FINISHED_JOBS = 'success', 'unknown', 'error'


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


# Register permissions on our models.
# These are part of the DB schema and should not be changed without serious
# forethought.
# You *must* syncdb after you change these.
register(permissions.CLUSTER_PARAMS, Cluster, 'ganeti_web')
register(permissions.VIRTUAL_MACHINE_PARAMS, VirtualMachine, 'ganeti_web')


# register log actions
register_log_actions()


def update_sites_module(sender, **kwargs):
    """
    Create a new row in the django_sites table that
      holds SITE_ID, SITE_NAME and SITE_DOMAIN defined
      in setting.py

      If SITE_NAME or SITE_DOMAIN are not defined they
       will default to 'example.com'
    """
    verb = kwargs.get('verbosity', 0)
    id, name, domain = (1, 'example.com', 'example.com')
    try:
        id = settings.SITE_ID
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site id.' % id

    try:
        name = settings.SITE_NAME
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site name.' % name

    try:
        domain = settings.SITE_DOMAIN
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site domain.' % domain

    try:
        site = Site.objects.get(id=id)
        if site.name != name:
            if verb >= 1:
                print "Site name changed from %s to %s." % \
                    (site.name, name)
            site.name = name
        if site.domain != domain:
            if verb >= 1:
                print "Site domain changed from %s to %s." % \
                    (site.domain, domain)
            site.domain = domain
        site.save()
    except Site.DoesNotExist:
        if verb >= 1:
            print "New site: [%s] %s (%s) created in django_site table." % \
                (id, name, domain)
        site = Site(id=id, name=name, domain=domain)
        site.save()
        # Reconnect create_default_site request for other apps
        post_syncdb.connect(create_default_site, sender=sites_app)
    else:
        if site.name != name:
            print "A site with the id of %s is already taken. " \
                  "Please change SITE_ID to a different number in your " \
                  "settings.py file." % id

# Disconnect create_default_site from django.contrib.sites so that
#  the useless table for sites is not created. This will be
#  reconnected for other apps to use in update_sites_module.
post_syncdb.disconnect(create_default_site, sender=sites_app)
post_syncdb.connect(update_sites_module, sender=sites_app,
                    dispatch_uid="ganeti.management.update_sites_module")
