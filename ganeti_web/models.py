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
import cPickle
from datetime import datetime, timedelta
from hashlib import sha1
import random
import re
import string
import sys

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

from ganeti_web.logs import register_log_actions

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from object_permissions.registration import register

from muddle_users import signals as muddle_user_signals

from ganeti_web import constants, management, permissions
from ganeti_web.fields import (PatchedEncryptedCharField,
                               PreciseDateTimeField, SumIf)
from ganeti_web.util import client
from ganeti_web.util.client import GanetiApiError, REPLACE_DISK_AUTO

from south.signals import post_migrate

if settings.VNC_PROXY:
    from ganeti_web.util.vncdaemon.vapclient import (request_forwarding,
                                                     request_ssh)


class QuerySetManager(models.Manager):
    """
    Useful if you want to define manager methods that need to chain. In this
    case create a QuerySet class within your model and add all of your methods
    directly to the queryset. Example:

    class Foo(models.Model):
        enabled = fields.BooleanField()
        dirty = fields.BooleanField()

        class QuerySet:
            def active(self):
                return self.filter(enabled=True)
            def clean(self):
                return self.filter(dirty=False)

    Foo.objects.active().clean()
    """

    def __getattr__(self, name, *args):
        # Cull under/dunder names to avoid certain kinds of recursion. Django
        # isn't super-bright here.
        if name.startswith('_'):
            raise AttributeError
        return getattr(self.get_query_set(), name, *args)

    def get_query_set(self):
        return self.model.QuerySet(self.model)


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


class CachedClusterObject(models.Model):
    """
    Parent class for objects which belong to Ganeti but have cached data in
    GWM.

    The main point of this class is to permit saving lots of data from Ganeti
    so that we don't have to look things up constantly. The Ganeti RAPI is
    slow, so avoiding it as much as possible is a good idea.

    This class provides transparent caching for all of the data that it
    serializes; no explicit cache accesses are required.

    This model is abstract and may not be instantiated on its own.
    """

    serialized_info = models.TextField(default="", editable=False)
    mtime = PreciseDateTimeField(null=True, editable=False)
    cached = PreciseDateTimeField(null=True, editable=False)
    ignore_cache = models.BooleanField(default=False)

    last_job_id = None
    __info = None
    error = None
    ctime = None
    deleted = False

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        overridden to ensure info is serialized prior to save
        """
        if not self.serialized_info:
            self.serialized_info = cPickle.dumps(self.__info)
        super(CachedClusterObject, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(CachedClusterObject, self).__init__(*args, **kwargs)
        self.load_info()

    @property
    def info(self):
        """
        A dictionary of metadata for this object.

        This is a proxy for the ``serialized_info`` field. Reads from this
        property lazily access the field, and writes to this property will be
        lazily saved.

        Writes to this property do *not* force serialization.
        """

        if self.__info is None:
            if self.serialized_info:
                self.__info = cPickle.loads(str(self.serialized_info))
        return self.__info

    def _set_info(self, value):
        self.__info = value
        if value is not None:
            self.parse_info()
            self.serialized_info = ""

    info = info.setter(_set_info)

    def load_info(self):
        """
        Load cached info retrieved from the ganeti cluster.  This function
        includes a lazy cache mechanism that uses a timer to decide whether or
        not to refresh the cached information with new information from the
        ganeti cluster.

        This will ignore the cache when self.ignore_cache is True
        """

        epsilon = timedelta(0, 0, 0, settings.LAZY_CACHE_REFRESH)

        if self.id:
            if (self.ignore_cache
                or self.cached is None
                or datetime.now() > self.cached + epsilon):
                self.refresh()
            elif self.info:
                self.parse_transient_info()
            else:
                self.error = 'No Cached Info'

    def parse_info(self):
        """
        Parse all of the attached metadata, and attach it to this object.
        """

        self.parse_transient_info()
        data = self.parse_persistent_info(self.info)
        for k in data:
            setattr(self, k, data[k])

    def refresh(self):
        """
        Retrieve and parse info from the ganeti cluster.  If successfully
        retrieved and parsed, this method will also call save().

        If communication with Ganeti fails, an error will be stored in
        ``error``.
        """

        job_data = self.check_job_status()
        for k, v in job_data.items():
            setattr(self, k, v)

        # XXX this try/except is far too big; see if we can pare it down.
        try:
            info_ = self._refresh()
            if info_:
                if info_['mtime']:
                    mtime = datetime.fromtimestamp(info_['mtime'])
                else:
                    mtime = None
                self.cached = datetime.now()
            else:
                # no info retrieved, use current mtime
                mtime = self.mtime

            if self.id and (self.mtime is None or mtime > self.mtime):
                # there was an update. Set info and save the object
                self.info = info_
                self.save()
            else:
                # There was no change on the server. Only update the cache
                # time. This bypasses the info serialization mechanism and
                # uses a smaller query.
                if job_data:
                    self.__class__.objects.filter(pk=self.id) \
                        .update(cached=self.cached, **job_data)
                elif self.id is not None:
                    self.__class__.objects.filter(pk=self.id) \
                        .update(cached=self.cached)

        except GanetiApiError, e:
            # Use regular expressions to match the quoted message
            #  given by GanetiApiError. '\\1' is a group substitution
            #  which places the first group '('|\")' in it's place.
            comp = re.compile("('|\")(?P<msg>.*)\\1")
            err = comp.search(str(e))
            # Any search that has 0 results will just return None.
            #   That is why we must check for err before proceeding.
            if err:
                msg = err.groupdict()['msg']
                self.error = msg
            else:
                msg = str(e)
                self.error = str(e)
            GanetiError.store_error(msg, obj=self, code=e.code)

        else:
            if self.error:
                self.error = None
                GanetiError.objects.clear_errors(obj=self)

    def _refresh(self):
        """
        Fetch raw data from the Ganeti cluster.

        This must be implemented by children of this class.
        """

        raise NotImplementedError

    def check_job_status(self):
        if not self.last_job_id:
            return {}

        ct = ContentType.objects.get_for_model(self)
        qs = Job.objects.filter(content_type=ct, object_id=self.pk)
        jobs = qs.order_by("job_id")

        updates = {}
        for job in jobs:
            status = 'unknown'
            op = None

            try:
                data = self.rapi.GetJobStatus(job.job_id)
                status = data['status']
                op = data['ops'][-1]['OP_ID']
            except GanetiApiError:
                pass

            if status in ('success', 'error'):
                for k, v in Job.parse_persistent_info(data).items():
                    setattr(job, k, v)

            if status == 'unknown':
                job.status = "unknown"
                job.ignore_cache = False

            if status in ('success', 'error', 'unknown'):
                _updates = self._complete_job(self.cluster_id,
                                              self.hostname, op, status)
                # XXX if the delete flag is set in updates then delete this
                # model this happens here because _complete_job cannot delete
                # this model
                if _updates:
                    if 'deleted' in _updates:
                        # Delete ourselves. Also delete the job that caused us
                        # to delete ourselves; see #8439 for "fun" details.
                        # Order matters; the job's deletion cascades over us.
                        # Revisit that when we finally nuke all this caching
                        # bullshit.
                        self.delete()
                        job.delete()
                    else:
                        updates.update(_updates)

        # we only care about the very last job for resetting the cache flags
        if status in ('success', 'error', 'unknown') or not jobs:
            updates['ignore_cache'] = False
            updates['last_job'] = None

        return updates

    @classmethod
    def _complete_job(cls, cluster_id, hostname, op, status):
        """
        Process a completed job.  This method will make any updates to related
        classes (like deleting an instance template) and return any data that
        should be updated.  This is a class method so that this processing can
        be done without a full instance.

        @returns dict of updated values
        """

        pass

    def parse_transient_info(self):
        """
        Parse properties from cached info that is stored on the class but not
        in the database.

        These properties will be loaded every time the object is instantiated.
        Properties stored on the class cannot be search efficiently via the
        django query api.

        This method is specific to the child object.
        """

        info_ = self.info
        # XXX ganeti 2.1 ctime is always None
        # XXX this means that we could nuke the conditionals!
        if info_['ctime'] is not None:
            self.ctime = datetime.fromtimestamp(info_['ctime'])

    @classmethod
    def parse_persistent_info(cls, info):
        """
        Parse properties from cached info that are stored in the database.

        These properties will be searchable by the django query api.

        This method is specific to the child object.
        """

        # mtime is sometimes None if object has never been modified
        if info['mtime'] is None:
            return {'mtime': None}
        return {'mtime': datetime.fromtimestamp(info['mtime'])}


class JobManager(models.Manager):
    """
    Custom manager for Ganeti Jobs model
    """
    def create(self, **kwargs):
        """ helper method for creating a job with disabled cache """
        job = Job(ignore_cache=True, **kwargs)
        job.save(force_insert=True)
        return job


class Job(CachedClusterObject):
    """
    model representing a job being run on a ganeti Cluster.  This includes
    operations such as creating or delting a virtual machine.

    Jobs are a special type of CachedClusterObject.  Job's run once then become
    immutable.  The lazy cache is modified to become permanent once a complete
    status (success/error) has been detected.  The cache can be disabled by
    settning ignore_cache=True.
    """

    job_id = models.IntegerField()
    content_type = models.ForeignKey(ContentType, related_name="+")
    object_id = models.IntegerField()
    obj = GenericForeignKey('content_type', 'object_id')
    cluster = models.ForeignKey('Cluster', related_name='jobs', editable=False)
    cluster_hash = models.CharField(max_length=40, editable=False)

    finished = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10)
    op = models.CharField(max_length=50)

    objects = JobManager()

    def save(self, *args, **kwargs):
        """
        sets the cluster_hash for newly saved instances
        """
        if self.id is None or self.cluster_hash == '':
            self.cluster_hash = self.cluster.hash

        super(Job, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        job = '%s/job/(?P<job_id>\d+)' % self.cluster

        return 'ganeti_web.views.jobs.detail', (), {'job': job}

    @property
    def rapi(self):
        return get_rapi(self.cluster_hash, self.cluster_id)

    def _refresh(self):
        return self.rapi.GetJobStatus(self.job_id)

    def load_info(self):
        """
        Load info for class.  This will load from ganeti if ignore_cache==True,
        otherwise this will always load from the cache.
        """
        if self.id and (self.ignore_cache or self.info is None):
            try:
                self.refresh()
            except GanetiApiError, e:
                # if the Job has been archived then we don't know whether it
                # was successful or not. Mark it as unknown.
                if e.code == 404:
                    self.status = 'unknown'
                    self.save()
                else:
                    # its possible the cluster or crednetials are bad. fail
                    # silently
                    pass

    def refresh(self):
        self.info = self._refresh()
        self.save()

    @classmethod
    def parse_persistent_info(cls, info):
        """
        Parse status and turn off cache bypass flag if job has finished
        """
        data = {'status': info['status'],
                'op': info['ops'][-1]['OP_ID']}
        if data['status'] in ('error', 'success'):
            data['ignore_cache'] = False
        if info['end_ts']:
            data['finished'] = cls.parse_end_timestamp(info)
        return data

    @staticmethod
    def parse_end_timestamp(info):
        sec, micro = info['end_ts']
        return datetime.fromtimestamp(sec + (micro / 1000000.0))

    def parse_transient_info(self):
        pass

    @property
    def current_operation(self):
        """
        Jobs may consist of multiple commands/operations.  This helper
        method will return the operation that is currently running or errored
        out, or the last operation if all operations have completed

        @returns raw name of the current operation
        """
        info = self.info
        index = 0
        for i in range(len(info['opstatus'])):
            if info['opstatus'][i] != 'success':
                index = i
                break
        return info['ops'][index]['OP_ID']

    @property
    def operation(self):
        """
        Returns the last operation, which is generally the primary operation.
        """
        return self.info['ops'][-1]['OP_ID']

    def __repr__(self):
        return "<Job %d (%d), status %r>" % (self.id, self.job_id,
                                             self.status)

    __unicode__ = __repr__


class VirtualMachine(CachedClusterObject):
    """
    The VirtualMachine (VM) model represents VMs within a Ganeti cluster.

    The majority of properties are a cache for data stored in the cluster.
    All data retrieved via the RAPI is stored in VirtualMachine.info, and
    serialized automatically into VirtualMachine.serialized_info.

    Attributes that need to be searchable should be stored as model fields.
    All other attributes will be stored within VirtualMachine.info.

    This object uses a lazy update mechanism on instantiation.  If the cached
    info from the Ganeti cluster has expired, it will trigger an update.  This
    allows the cache to function in the absence of a periodic update mechanism
    such as Cron, Celery, or Threads.

    The lazy update and periodic update should use separate refresh timeouts
    where LAZY_CACHE_REFRESH > PERIODIC_CACHE_REFRESH.  This ensures that lazy
    cache will only be used if the periodic cache is not updating.

    XXX Serialized_info can possibly be changed to a CharField if an upper
        limit can be determined. (Later Date, if it will optimize db)

    """
    cluster = models.ForeignKey('Cluster', related_name='virtual_machines',
                                editable=False, default=0)
    hostname = models.CharField(max_length=128, db_index=True)
    owner = models.ForeignKey('ClusterUser', related_name='virtual_machines',
                              null=True, blank=True,
                              on_delete=models.SET_NULL)
    virtual_cpus = models.IntegerField(default=-1)
    disk_size = models.IntegerField(default=-1)
    ram = models.IntegerField(default=-1)
    cluster_hash = models.CharField(max_length=40, editable=False)
    operating_system = models.CharField(max_length=128)
    status = models.CharField(max_length=14)

    # node relations
    primary_node = models.ForeignKey('Node', related_name='primary_vms',
                                     null=True, blank=True)
    secondary_node = models.ForeignKey('Node', related_name='secondary_vms',
                                       null=True, blank=True)

    # The last job reference indicates that there is at least one pending job
    # for this virtual machine.  There may be more than one job, and that can
    # never be prevented.  This just indicates that job(s) are pending and the
    # job related code should be run (status, cleanup, etc).
    last_job = models.ForeignKey('Job', related_name="+", null=True,
                                 blank=True)

    # deleted flag indicates a VM is being deleted, but the job has not
    # completed yet.  VMs that have pending_delete are still displayed in lists
    # and counted in quotas, but only so status can be checked.
    pending_delete = models.BooleanField(default=False)
    deleted = False

    # Template temporarily stores parameters used to create this virtual
    # machine. This template is used to recreate the values entered into the
    # form.
    template = models.ForeignKey("VirtualMachineTemplate",
                                 related_name="instances", null=True,
                                 blank=True)

    class Meta:
        ordering = ["hostname"]
        unique_together = (("cluster", "hostname"),)

    def __unicode__(self):
        return self.hostname

    def save(self, *args, **kwargs):
        """
        sets the cluster_hash for newly saved instances
        """
        if self.id is None:
            self.cluster_hash = self.cluster.hash

        info_ = self.info
        if info_:
            found = False
            remove = []
            if self.cluster.username:
                for tag in info_['tags']:
                    # Update owner Tag. Make sure the tag is set to the owner
                    #  that is set in webmgr.
                    if tag.startswith(constants.OWNER_TAG):
                        id = int(tag[len(constants.OWNER_TAG):])
                        # Since there is no 'update tag' delete old tag and
                        #  replace with tag containing correct owner id.
                        if id == self.owner_id:
                            found = True
                        else:
                            remove.append(tag)
                if remove:
                    self.rapi.DeleteInstanceTags(self.hostname, remove)
                    for tag in remove:
                        info_['tags'].remove(tag)
                if self.owner_id and not found:
                    tag = '%s%s' % (constants.OWNER_TAG, self.owner_id)
                    self.rapi.AddInstanceTags(self.hostname, [tag])
                    self.info['tags'].append(tag)

        super(VirtualMachine, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        """
        Return absolute url for this instance.
        """

        return 'instance-detail', (), {'cluster_slug': self.cluster.slug,
                                       'instance': self.hostname}

    @property
    def rapi(self):
        return get_rapi(self.cluster_hash, self.cluster_id)

    @property
    def is_running(self):
        return self.status == 'running'

    @classmethod
    def parse_persistent_info(cls, info):
        """
        Loads all values from cached info, included persistent properties that
        are stored in the database
        """
        data = super(VirtualMachine, cls).parse_persistent_info(info)

        # Parse resource properties
        data['ram'] = info['beparams']['memory']
        data['virtual_cpus'] = info['beparams']['vcpus']
        # Sum up the size of each disk used by the VM
        disk_size = 0
        for disk in info['disk.sizes']:
            disk_size += disk
        data['disk_size'] = disk_size
        data['operating_system'] = info['os']
        data['status'] = info['status']

        primary = info['pnode']
        if primary:
            try:
                data['primary_node'] = Node.objects.get(hostname=primary)
            except Node.DoesNotExist:
                # node is not created yet.  fail silently
                data['primary_node'] = None
        else:
            data['primary_node'] = None

        secondary = info['snodes']
        if len(secondary):
            secondary = secondary[0]
            try:
                data['secondary_node'] = Node.objects.get(hostname=secondary)
            except Node.DoesNotExist:
                # node is not created yet.  fail silently
                data['secondary_node'] = None
        else:
            data['secondary_node'] = None

        return data

    @classmethod
    def _complete_job(cls, cluster_id, hostname, op, status):
        """
        if the cache bypass is enabled then check the status of the last job
        when the job is complete we can reenable the cache.

        @returns - dictionary of values that were updates
        """

        if status == 'unknown':
            # unknown status, the job was archived before it's final status
            # was polled.  Impossible to tell what happened.  Clear the job
            # so it is no longer polled.
            #
            # XXX This VM might be added by the CLI and be in an invalid
            # pending_delete state.  clearing pending_delete prevents this
            # but will result in "missing" vms in some cases.
            return dict(pending_delete=False)

        base = VirtualMachine.objects.filter(cluster=cluster_id,
                                             hostname=hostname)
        if op == 'OP_INSTANCE_REMOVE':
            if status == 'success':
                # XXX can't actually delete here since it would cause a
                # recursive loop
                return dict(deleted=True)

        elif op == 'OP_INSTANCE_CREATE' and status == 'success':
            # XXX must update before deleting the template to maintain
            # referential integrity.  as a consequence return no other
            # updates.
            base.update(template=None)
            VirtualMachineTemplate.objects \
                .filter(instances__hostname=hostname,
                        instances__cluster=cluster_id) \
                .delete()
            return dict(template=None)
        return

    def _refresh(self):
        # XXX if delete is pending then no need to refresh this object.
        if self.pending_delete or self.template_id:
            return None
        return self.rapi.GetInstance(self.hostname)

    def shutdown(self, timeout=None):
        if timeout is None:
            id = self.rapi.ShutdownInstance(self.hostname)
        else:
            id = self.rapi.ShutdownInstance(self.hostname, timeout=timeout)

        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def startup(self):
        id = self.rapi.StartupInstance(self.hostname)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def reboot(self):
        id = self.rapi.RebootInstance(self.hostname)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def migrate(self, mode='live', cleanup=False):
        """
        Migrates this VirtualMachine to another node.

        Only works if the disk type is DRDB.

        @param mode: live or non-live
        @param cleanup: clean up a previous migration, default is False
        """
        id = self.rapi.MigrateInstance(self.hostname, mode, cleanup)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def replace_disks(self, mode=REPLACE_DISK_AUTO, disks=None, node=None,
                      iallocator=None):
        id = self.rapi.ReplaceInstanceDisks(self.hostname, disks, mode, node,
                                            iallocator)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def setup_ssh_forwarding(self, sport=0):
        """
        Poke a proxy to start SSH forwarding.

        Returns None if no proxy is configured, or if there was an error
        contacting the proxy.
        """

        command = self.rapi.GetInstanceConsole(self.hostname)["command"]

        if settings.VNC_PROXY:
            proxy_server = settings.VNC_PROXY.split(":")
            password = generate_random_password()
            sport = request_ssh(proxy_server, sport, self.info["pnode"],
                                self.info["network_port"], password, command)

            if sport:
                return proxy_server[0], sport, password

    def setup_vnc_forwarding(self, sport=0, tls=False):
        """
        Obtain VNC forwarding information, optionally configuring a proxy.

        Returns None if a proxy is configured and there was an error
        contacting the proxy.
        """

        password = ''
        info_ = self.info
        port = info_['network_port']
        node = info_['pnode']

        # use proxy for VNC connection
        if settings.VNC_PROXY:
            proxy_server = settings.VNC_PROXY.split(":")
            password = generate_random_password()
            result = request_forwarding(proxy_server, node, port, password,
                                        sport=sport, tls=tls)
            if result:
                return proxy_server[0], int(result), password
        else:
            return node, port, password

    def __repr__(self):
        return "<VirtualMachine: '%s'>" % self.hostname


class Node(CachedClusterObject):
    """
    The Node model represents nodes within a Ganeti cluster.

    The majority of properties are a cache for data stored in the cluster.
    All data retrieved via the RAPI is stored in VirtualMachine.info, and
    serialized automatically into VirtualMachine.serialized_info.

    Attributes that need to be searchable should be stored as model fields.
    All other attributes will be stored within VirtualMachine.info.
    """

    ROLE_CHOICES = ((k, v) for k, v in constants.NODE_ROLE_MAP.items())

    cluster = models.ForeignKey('Cluster', related_name='nodes')
    hostname = models.CharField(max_length=128, unique=True)
    cluster_hash = models.CharField(max_length=40, editable=False)
    offline = models.BooleanField()
    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    ram_total = models.IntegerField(default=-1)
    ram_free = models.IntegerField(default=-1)
    disk_total = models.IntegerField(default=-1)
    disk_free = models.IntegerField(default=-1)
    cpus = models.IntegerField(null=True, blank=True)

    # The last job reference indicates that there is at least one pending job
    # for this virtual machine.  There may be more than one job, and that can
    # never be prevented.  This just indicates that job(s) are pending and the
    # job related code should be run (status, cleanup, etc).
    last_job = models.ForeignKey('Job', related_name="+", null=True,
                                 blank=True)

    def __unicode__(self):
        return self.hostname

    def save(self, *args, **kwargs):
        """
        sets the cluster_hash for newly saved instances
        """
        if self.id is None:
            self.cluster_hash = self.cluster.hash
        super(Node, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        """
        Return absolute url for this node.
        """

        return 'node-detail', (), {'cluster_slug': self.cluster.slug,
                                   'host': self.hostname}

    def _refresh(self):
        """ returns node info from the ganeti server """
        return self.rapi.GetNode(self.hostname)

    @property
    def rapi(self):
        return get_rapi(self.cluster_hash, self.cluster_id)

    @classmethod
    def parse_persistent_info(cls, info):
        """
        Loads all values from cached info, included persistent properties that
        are stored in the database
        """
        data = super(Node, cls).parse_persistent_info(info)

        # Parse resource properties
        data['ram_total'] = info.get("mtotal") or 0
        data['ram_free'] = info.get("mfree") or 0
        data['disk_total'] = info.get("dtotal") or 0
        data['disk_free'] = info.get("dfree") or 0
        data['cpus'] = info.get("csockets")
        data['offline'] = info['offline']
        data['role'] = info['role']
        return data

    @property
    def ram(self):
        """ returns dict of free and total ram """
        values = VirtualMachine.objects \
            .filter(Q(primary_node=self) | Q(secondary_node=self)) \
            .filter(status='running') \
            .exclude(ram=-1).order_by() \
            .aggregate(used=Sum('ram'))

        total = self.ram_total
        used = total - self.ram_free
        allocated = values.get("used") or 0
        free = total - allocated if allocated >= 0 and total >= 0 else -1

        return {
            'total': total,
            'free':  free,
            'allocated': allocated,
            'used': used,
        }

    @property
    def disk(self):
        """ returns dict of free and total disk space """
        values = VirtualMachine.objects \
            .filter(Q(primary_node=self) | Q(secondary_node=self)) \
            .exclude(disk_size=-1).order_by() \
            .aggregate(used=Sum('disk_size'))

        total = self.disk_total
        used = total - self.disk_free
        allocated = values.get("used") or 0
        free = total - allocated if allocated >= 0 and total >= 0 else -1

        return {
            'total': total,
            'free':  free,
            'allocated': allocated,
            'used': used,
        }

    @property
    def allocated_cpus(self):
        values = VirtualMachine.objects \
            .filter(primary_node=self, status='running') \
            .exclude(virtual_cpus=-1).order_by() \
            .aggregate(cpus=Sum('virtual_cpus'))
        return values.get("cpus") or 0

    def set_role(self, role, force=False):
        """
        Sets the role for this node

        @param role - one of the following choices:
            * master
            * master-candidate
            * regular
            * drained
            * offline
        """
        id = self.rapi.SetNodeRole(self.hostname, role, force)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        Node.objects.filter(pk=self.pk).update(ignore_cache=True, last_job=job)
        return job

    def evacuate(self, iallocator=None, node=None):
        """
        migrates all secondary instances off this node
        """
        id = self.rapi.EvacuateNode(self.hostname, iallocator=iallocator,
                                    remote_node=node)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        Node.objects.filter(pk=self.pk) \
            .update(ignore_cache=True, last_job=job)
        return job

    def migrate(self, mode=None):
        """
        migrates all primary instances off this node
        """
        id = self.rapi.MigrateNode(self.hostname, mode)
        job = Job.objects.create(job_id=id, obj=self,
                                 cluster_id=self.cluster_id)
        self.last_job = job
        Node.objects.filter(pk=self.pk).update(ignore_cache=True, last_job=job)
        return job

    def __repr__(self):
        return "<Node: '%s'>" % self.hostname


class Cluster(CachedClusterObject):
    """
    A Ganeti cluster that is being tracked by this manager tool
    """
    hostname = models.CharField(_('hostname'), max_length=128, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True,
                            db_index=True)
    port = models.PositiveIntegerField(_('port'), default=5080)
    description = models.CharField(_('description'), max_length=128,
                                   blank=True)
    username = models.CharField(_('username'), max_length=128, blank=True)
    password = PatchedEncryptedCharField(_('password'), default="",
                                         max_length=128, blank=True)
    hash = models.CharField(_('hash'), max_length=40, editable=False)

    # quota properties
    virtual_cpus = models.IntegerField(_('Virtual CPUs'), null=True,
                                       blank=True)
    disk = models.IntegerField(_('disk'), null=True, blank=True)
    ram = models.IntegerField(_('ram'), null=True, blank=True)

    # The last job reference indicates that there is at least one pending job
    # for this virtual machine.  There may be more than one job, and that can
    # never be prevented.  This just indicates that job(s) are pending and the
    # job related code should be run (status, cleanup, etc).
    last_job = models.ForeignKey('Job', related_name='cluster_last_job',
                                 null=True, blank=True)

    class Meta:
        ordering = ["hostname", "description"]

    def __unicode__(self):
        return self.hostname

    def save(self, *args, **kwargs):
        self.hash = self.create_hash()
        super(Cluster, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'cluster-detail', (), {'cluster_slug': self.slug}

    # XXX probably hax
    @property
    def cluster_id(self):
        return self.id

    @classmethod
    def decrypt_password(cls, value):
        """
        Convenience method for decrypting a password without an instance.
        This was partly cribbed from django-fields which only allows decrypting
        from a model instance.

        If the password appears to be encrypted, this method will decrypt it;
        otherwise, it will return the password unchanged.

        This method is bonghits.
        """

        field, chaff, chaff, chaff = cls._meta.get_field_by_name('password')

        if value.startswith(field.prefix):
            ciphertext = value[len(field.prefix):]
            plaintext = field.cipher.decrypt(binascii.a2b_hex(ciphertext))
            password = plaintext.split('\0')[0]
        else:
            password = value

        return force_unicode(password)

    @property
    def rapi(self):
        """
        retrieves the rapi client for this cluster.
        """
        # XXX always pass self in.  not only does it avoid querying this object
        # from the DB a second time, it also prevents a recursion loop caused
        # by __init__ fetching info from the Cluster
        return get_rapi(self.hash, self)

    def create_hash(self):
        """
        Creates a hash for this cluster based on credentials required for
        connecting to the server
        """
        s = '%s%s%s%s' % (self.username, self.password, self.hostname,
                          self.port)
        return sha1(s).hexdigest()

    def get_default_quota(self):
        """
        Returns the default quota for this cluster
        """
        return {
            "default": 1,
            "ram": self.ram,
            "disk": self.disk,
            "virtual_cpus": self.virtual_cpus,
        }

    def get_quota(self, user=None):
        """
        Get the quota for a ClusterUser

        @return user's quota, default quota, or none
        """
        if user is None:
            return self.get_default_quota()

        # attempt to query user specific quota first. if it does not exist
        # then fall back to the default quota
        query = Quota.objects.filter(cluster=self, user=user)
        quotas = query.values('ram', 'disk', 'virtual_cpus')
        if quotas:
            quota = quotas[0]
            quota['default'] = 0
            return quota

        return self.get_default_quota()

    def set_quota(self, user, data):
        """
        Set the quota for a ClusterUser.

        If data is None, the quota will be removed.

        @param values: dictionary of values, or None to delete the quota
        """

        kwargs = {'cluster': self, 'user': user}
        if data is None:
            Quota.objects.filter(**kwargs).delete()
        else:
            quota, new = Quota.objects.get_or_create(**kwargs)
            quota.__dict__.update(data)
            quota.save()

    @classmethod
    def get_quotas(cls, clusters=None, user=None):
        """ retrieve a bulk list of cluster quotas """

        if clusters is None:
            clusters = Cluster.objects.all()

        quotas = {}
        cluster_id_map = {}
        for cluster in clusters:
            quotas[cluster] = {
                'default': 1,
                'ram': cluster.ram,
                'disk': cluster.disk,
                'virtual_cpus': cluster.virtual_cpus,
            }
            cluster_id_map[cluster.id] = cluster

        # get user's custom queries if any
        if user is not None:
            qs = Quota.objects.filter(cluster__in=clusters, user=user)
            values = qs.values('ram', 'disk', 'virtual_cpus', 'cluster__id')

            for custom in values:
                try:
                    cluster = cluster_id_map[custom['cluster__id']]
                except KeyError:
                    continue
                custom['default'] = 0
                del custom['cluster__id']
                quotas[cluster] = custom

        return quotas

    def sync_virtual_machines(self, remove=False):
        """
        Synchronizes the VirtualMachines in the database with the information
        this ganeti cluster has:
            * VMs no longer in ganeti are deleted
            * VMs missing from the database are added
        """
        ganeti = self.instances()
        db = self.virtual_machines.all().values_list('hostname', flat=True)

        # add VMs missing from the database
        for hostname in filter(lambda x: unicode(x) not in db, ganeti):
            vm = VirtualMachine.objects.create(cluster=self, hostname=hostname)
            vm.refresh()

        # deletes VMs that are no longer in ganeti
        if remove:
            missing_ganeti = filter(lambda x: str(x) not in ganeti, db)
            if missing_ganeti:
                self.virtual_machines \
                    .filter(hostname__in=missing_ganeti).delete()

    def sync_nodes(self, remove=False):
        """
        Synchronizes the Nodes in the database with the information
        this ganeti cluster has:
            * Nodes no longer in ganeti are deleted
            * Nodes missing from the database are added
        """
        ganeti = self.rapi.GetNodes()
        db = self.nodes.all().values_list('hostname', flat=True)

        # add Nodes missing from the database
        for hostname in filter(lambda x: unicode(x) not in db, ganeti):
            node = Node.objects.create(cluster=self, hostname=hostname)
            node.refresh()

        # deletes Nodes that are no longer in ganeti
        if remove:
            missing_ganeti = filter(lambda x: str(x) not in ganeti, db)
            if missing_ganeti:
                self.nodes.filter(hostname__in=missing_ganeti).delete()

    @property
    def missing_in_ganeti(self):
        """
        Returns a list of VirtualMachines that are missing from the Ganeti
        cluster but present in the database.
        """
        ganeti = self.instances()
        qs = self.virtual_machines.exclude(template__isnull=False)
        db = qs.values_list('hostname', flat=True)
        return [x for x in db if str(x) not in ganeti]

    @property
    def missing_in_db(self):
        """
        Returns list of VirtualMachines that are missing from the database, but
        present in ganeti
        """
        ganeti = self.instances()
        db = self.virtual_machines.all().values_list('hostname', flat=True)
        return [x for x in ganeti if unicode(x) not in db]

    @property
    def nodes_missing_in_db(self):
        """
        Returns list of Nodes that are missing from the database, but present
        in ganeti.
        """
        try:
            ganeti = self.rapi.GetNodes()
        except GanetiApiError:
            ganeti = []
        db = self.nodes.all().values_list('hostname', flat=True)
        return [x for x in ganeti if unicode(x) not in db]

    @property
    def nodes_missing_in_ganeti(self):
        """
        Returns list of Nodes that are missing from the ganeti cluster
        but present in the database
        """
        try:
            ganeti = self.rapi.GetNodes()
        except GanetiApiError:
            ganeti = []
        db = self.nodes.all().values_list('hostname', flat=True)
        return filter(lambda x: str(x) not in ganeti, db)

    @property
    def available_ram(self):
        """ returns dict of free and total ram """
        nodes = self.nodes.exclude(ram_total=-1) \
            .aggregate(total=Sum('ram_total'), free=Sum('ram_free'))
        total = max(nodes.get("total", 0), 0)
        free = max(nodes.get("free", 0), 0)
        used = total - free
        values = self.virtual_machines \
            .filter(status='running') \
            .exclude(ram=-1).order_by() \
            .aggregate(used=Sum('ram'))

        if values.get("used") is None:
            allocated = 0
        else:
            allocated = values["used"]

        free = max(total - allocated, 0)

        return {
            'total': total,
            'free': free,
            'allocated': allocated,
            'used': used,
        }

    @property
    def available_disk(self):
        """ returns dict of free and total disk space """
        nodes = self.nodes.exclude(disk_total=-1) \
            .aggregate(total=Sum('disk_total'), free=Sum('disk_free'))
        total = max(nodes.get("total", 0), 0)
        free = max(nodes.get("free", 0), 0)
        used = total - free
        values = self.virtual_machines \
            .exclude(disk_size=-1).order_by() \
            .aggregate(used=Sum('disk_size'))

        if values.get("used") is None:
            allocated = 0
        else:
            allocated = values["used"]

        free = max(total - allocated, 0)

        return {
            'total': total,
            'free': free,
            'allocated': allocated,
            'used': used,
        }

    def _refresh(self):
        return self.rapi.GetInfo()

    def instances(self, bulk=False):
        """Gets all VMs which reside under the Cluster
        Calls the rapi client for all instances.
        """
        try:
            return self.rapi.GetInstances(bulk=bulk)
        except GanetiApiError:
            return []

    def instance(self, instance):
        """Get a single Instance
        Calls the rapi client for a specific instance.
        """
        try:
            return self.rapi.GetInstance(instance)
        except GanetiApiError:
            return None

    def redistribute_config(self):
        """
        Redistribute config from cluster's master node to all
        other nodes.
        """
        # no exception handling, because it's being done in a view
        id = self.rapi.RedistributeConfig()
        job = Job.objects.create(job_id=id, obj=self, cluster_id=self.id)
        self.last_job = job
        Cluster.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job


class VirtualMachineTemplate(models.Model):
    """
    Virtual Machine Template holds all the values for the create virtual
    machine form so that they can automatically be used or edited by a user.
    """

    template_name = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=255, default="")
    cluster = models.ForeignKey(Cluster, related_name="templates", null=True,
                                blank=True)
    start = models.BooleanField(verbose_name=_('Start up After Creation'),
                                default=True)
    no_install = models.BooleanField(verbose_name=_('Do not install OS'),
                                     default=False)
    ip_check = BooleanField(verbose_name=_("IP Check"), default=True)
    name_check = models.BooleanField(verbose_name=_('DNS Name Check'),
                                     default=True)
    iallocator = models.BooleanField(verbose_name=_('Automatic Allocation'),
                                     default=False)
    iallocator_hostname = models.CharField(max_length=255, blank=True)
    disk_template = models.CharField(verbose_name=_('Disk Template'),
                                     max_length=16)
    # XXX why aren't these FKs?
    pnode = models.CharField(verbose_name=_('Primary Node'), max_length=255,
                             default="")
    snode = models.CharField(verbose_name=_('Secondary Node'), max_length=255,
                             default="")
    os = models.CharField(verbose_name=_('Operating System'), max_length=255)

    # Backend parameters (BEPARAMS)
    vcpus = models.IntegerField(verbose_name=_('Virtual CPUs'),
                                validators=[MinValueValidator(1)], null=True,
                                blank=True)
    # XXX do we really want the minimum memory to be 100MiB? This isn't
    # strictly necessary AFAICT.
    memory = models.IntegerField(verbose_name=_('Memory'),
                                 validators=[MinValueValidator(100)],
                                 null=True, blank=True)
    disks = PickleField(verbose_name=_('Disks'), null=True, blank=True)
    # XXX why isn't this an enum?
    disk_type = models.CharField(verbose_name=_('Disk Type'), max_length=255,
                                default="")
    nics = PickleField(verbose_name=_('NICs'), null=True, blank=True)
    # XXX why isn't this an enum?
    nic_type = models.CharField(verbose_name=_('NIC Type'), max_length=255,
                                default="")

    # Hypervisor parameters (HVPARAMS)
    kernel_path = models.CharField(verbose_name=_('Kernel Path'),
                                   max_length=255, default="", blank=True)
    root_path = models.CharField(verbose_name=_('Root Path'), max_length=255,
                                 default='/', blank=True)
    serial_console = models.BooleanField(
        verbose_name=_('Enable Serial Console'))
    boot_order = models.CharField(verbose_name=_('Boot Device'),
                                  max_length=255, default="")
    cdrom_image_path = models.CharField(verbose_name=_('CD-ROM Image Path'),
                                        max_length=512, blank=True)
    cdrom2_image_path = models.CharField(
        verbose_name=_('CD-ROM 2 Image Path'),
        max_length=512, blank=True)

    class Meta:
        unique_together = (("cluster", "template_name"),)

    def __unicode__(self):
        if self.template_name is None:
            return u'unnamed'
        else:
            return self.template_name


class GanetiError(models.Model):
    """
    Class for storing errors which occured in Ganeti
    """
    cluster = models.ForeignKey(Cluster, related_name="errors")
    msg = models.TextField()
    code = models.PositiveIntegerField(blank=True, null=True)

    # XXX could be fixed with django-model-util's TimeStampedModel
    timestamp = models.DateTimeField()

    # determines if the errors still appears or not
    cleared = models.BooleanField(default=False)

    # cluster object (cluster, VM, Node) affected by the error (if any)
    obj_type = models.ForeignKey(ContentType, related_name="ganeti_errors")
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey("obj_type", "obj_id")

    objects = QuerySetManager()

    class Meta:
        ordering = ("-timestamp", "code", "msg")

    def __unicode__(self):
        base = u"[%s] %s" % (self.timestamp, self.msg)
        return base

    class QuerySet(QuerySet):

        def clear_errors(self, obj=None):
            """
            Clear errors instead of deleting them.
            """

            qs = self.filter(cleared=False)

            if obj:
                qs = qs.get_errors(obj)

            return qs.update(cleared=True)

        def get_errors(self, obj):
            """
            Manager method used for getting QuerySet of all errors depending
            on passed arguments.

            @param  obj   affected object (itself or just QuerySet)
            """

            if obj is None:
                raise RuntimeError("Implementation error calling get_errors()"
                                   "with None")

            # Create base query of errors to return.
            #
            # if it's a Cluster or a queryset for Clusters, then we need to
            # get all errors from the Clusters. Do this by filtering on
            # GanetiError.cluster instead of obj_id.
            if isinstance(obj, (Cluster,)):
                return self.filter(cluster=obj)

            elif isinstance(obj, (QuerySet,)):
                if obj.model == Cluster:
                    return self.filter(cluster__in=obj)
                else:
                    ct = ContentType.objects.get_for_model(obj.model)
                    return self.filter(obj_type=ct, obj_id__in=obj)

            else:
                ct = ContentType.objects.get_for_model(obj.__class__)
                return self.filter(obj_type=ct, obj_id=obj.pk)

    def __repr__(self):
        return "<GanetiError '%s'>" % self.msg

    @classmethod
    def store_error(cls, msg, obj, code, **kwargs):
        """
        Create and save an error with the given information.

        @param  msg  error's message
        @param  obj  object (i.e. cluster or vm) affected by the error
        @param code  error's code number
        """
        ct = ContentType.objects.get_for_model(obj.__class__)
        is_cluster = isinstance(obj, Cluster)

        # 401 -- bad permissions
        # 401 is cluster-specific error and thus shouldn't appear on any other
        # object.
        if code == 401:
            if not is_cluster:
                # NOTE: what we do here is almost like:
                #  return self.store_error(msg=msg, code=code, obj=obj.cluster)
                # we just omit the recursiveness
                obj = obj.cluster
                ct = ContentType.objects.get_for_model(Cluster)
                is_cluster = True

        # 404 -- object not found
        # 404 can occur on any object, but when it occurs on a cluster, then
        # any of its children must not see the error again
        elif code == 404:
            if not is_cluster:
                # return if the error exists for cluster
                try:
                    c_ct = ContentType.objects.get_for_model(Cluster)
                    return cls.objects.get(msg=msg, obj_type=c_ct, code=code,
                                           obj_id=obj.cluster_id,
                                           cleared=False)

                except cls.DoesNotExist:
                    # we want to proceed when the error is not
                    # cluster-specific
                    pass

        # XXX use a try/except instead of get_or_create().  get_or_create()
        # does not allow us to set cluster_id.  This means we'd have to query
        # the cluster object to create the error.  we can't guaranteee the
        # cluster will already be queried so use create() instead which does
        # allow cluster_id
        try:
            return cls.objects.get(msg=msg, obj_type=ct, obj_id=obj.pk,
                                   code=code, **kwargs)

        except cls.DoesNotExist:
            cluster_id = obj.pk if is_cluster else obj.cluster_id

            return cls.objects.create(timestamp=datetime.now(), msg=msg,
                                      obj_type=ct, obj_id=obj.pk,
                                      cluster_id=cluster_id, code=code,
                                      **kwargs)


class ClusterUser(models.Model):
    """
    Base class for objects that may interact with a Cluster or VirtualMachine.
    """

    name = models.CharField(max_length=128)
    real_type = models.ForeignKey(ContentType, related_name="+",
                                  editable=False, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(ClusterUser, self).save(*args, **kwargs)

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        raise self.cast().permissable

    @classmethod
    def _get_real_type(cls):
        return ContentType.objects.get_for_model(cls)

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    def used_resources(self, cluster=None, only_running=True):
        """
        Return dictionary of total resources used by VMs that this ClusterUser
        has perms to.
        @param cluster  if set, get only VMs from specified cluster
        @param only_running  if set, get only running VMs
        """
        # XXX - order_by must be cleared or it breaks annotation grouping since
        #       the default order_by field is also added to the group_by clause
        base = self.virtual_machines.all().order_by()

        # XXX - use a custom aggregate for ram and vcpu count when filtering by
        # running.  this allows us to execute a single query.
        #
        # XXX - quotes must be used in this order.  postgresql quirk
        if only_running:
            sum_ram = SumIf('ram', condition="status='running'")
            sum_vcpus = SumIf('virtual_cpus', condition="status='running'")
        else:
            sum_ram = Sum('ram')
            sum_vcpus = Sum('virtual_cpus')

        base = base.exclude(ram=-1, disk_size=-1, virtual_cpus=-1)

        if cluster:
            base = base.filter(cluster=cluster)
            result = base.aggregate(ram=sum_ram, disk=Sum('disk_size'),
                                    virtual_cpus=sum_vcpus)

            # repack with zeros instead of Nones
            if result['disk'] is None:
                result['disk'] = 0
            if result['ram'] is None:
                result['ram'] = 0
            if result['virtual_cpus'] is None:
                result['virtual_cpus'] = 0
            return result

        else:
            base = base.values('cluster').annotate(uram=sum_ram,
                                                   udisk=Sum('disk_size'),
                                                   uvirtual_cpus=sum_vcpus)

            # repack as dictionary
            result = {}
            for used in base:
                # repack with zeros instead of Nones, change index names
                used["ram"] = used.pop("uram") or 0
                used["disk"] = used.pop("udisk") or 0
                used["virtual_cpus"] = used.pop("uvirtual_cpus") or 0
                result[used.pop('cluster')] = used

            return result


class Profile(ClusterUser):
    """
    Profile associated with a django.contrib.auth.User object.
    """
    user = models.OneToOneField(User)

    @models.permalink
    def get_absolute_url(self):
        return ('muddle_users.views.user')

    def grant(self, perm, obj):
        self.user.grant(perm, obj)

    def set_perms(self, perms, obj):
        self.user.set_perms(perms, obj)

    def get_objects_any_perms(self, *args, **kwargs):
        return self.user.get_objects_any_perms(*args, **kwargs)

    def has_perm(self, *args, **kwargs):
        return self.user.has_perm(*args, **kwargs)

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        return self.user


class Organization(ClusterUser):
    """
    An organization is used for grouping Users.

    Organizations are matched with an instance of contrib.auth.models.Group.
    This model exists so that contrib.auth.models.Group have a 1:1 relation
    with a ClusterUser on which quotas and permissions can be assigned.
    """

    group = models.OneToOneField(Group, related_name='organization')

    def grant(self, perm, object):
        self.group.grant(perm, object)

    def set_perms(self, perms, object):
        self.group.set_perms(perms, object)

    def get_objects_any_perms(self, *args, **kwargs):
        return self.group.get_objects_any_perms(*args, **kwargs)

    def has_perm(self, *args, **kwargs):
        return self.group.has_perm(*args, **kwargs)

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        return self.group


class Quota(models.Model):
    """
    A resource limit imposed on a ClusterUser for a given Cluster.  The
    attributes of this model represent maximum values the ClusterUser can
    consume.  The absence of a Quota indicates unlimited usage.
    """
    user = models.ForeignKey(ClusterUser, related_name='quotas')
    cluster = models.ForeignKey(Cluster, related_name='quotas')

    ram = models.IntegerField(default=0, null=True, blank=True)
    disk = models.IntegerField(default=0, null=True, blank=True)
    virtual_cpus = models.IntegerField(default=0, null=True, blank=True)


class SSHKey(models.Model):
    """
    Model representing user's SSH public key. Virtual machines rely on
    many ssh keys.
    """
    key = models.TextField(validators=[validate_sshkey])
    #filename = models.CharField(max_length=128) # saves key file's name
    user = models.ForeignKey(User, related_name='ssh_keys')


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
