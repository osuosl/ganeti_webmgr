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


import cPickle
from datetime import datetime, timedelta
from hashlib import sha1

from django.conf import settings

from django.contrib.sites import models as sites_app
from django.contrib.sites.management import create_default_site
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from django.core.validators import RegexValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _
import re

from django.db import models
from django.db.models import Sum, F, Q
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, post_syncdb
from django.db.utils import DatabaseError

from logs.models import LogItem
log_action = LogItem.objects.log_action

from object_permissions.registration import register
from object_permissions import signals as op_signals

from ganeti import constants, management
from ganeti.fields import PreciseDateTimeField
from ganeti import permissions
from util import client
from util.client import GanetiApiError

if settings.VNC_PROXY:
    from util.vncdaemon.vapclient import request_forwarding
import random
import string

def generate_random_password(length=12):
    "Generate random sequence of specified length"
    return "".join( random.sample(string.letters + string.digits, length) )

RAPI_CACHE = {}
RAPI_CACHE_HASHES = {}
def get_rapi(hash, cluster):
    """
    Retrieves the cached Ganeti RAPI client for a given hash.  The Hash is
    derived from the connection credentials required for a cluster.  If the
    client is not yet cached, it will be created and added.

    If a hash does not correspond to any cluster then Cluster.DoesNotExist will
    be raised.

    @param cluster - either a cluster object, or ID of object.  This is used for
        resolving the cluster if the client is not already found.  The id is
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
        .values_list('hash','hostname','port','username','password')
    hash, host, port, user, password = credentials
    user = user if user else None
    password = password if password else None

    # now that we know hash is fresh, check cache again. The original hash could
    # have been stale.  This avoids constructing a new RAPI that already exists.
    if hash in RAPI_CACHE:
        return RAPI_CACHE[hash]

    # delete any old version of the client that was cached.
    if cluster in RAPI_CACHE_HASHES:
        del RAPI_CACHE[RAPI_CACHE_HASHES[cluster]]

    rapi = client.GanetiRapiClient(host, port, user, password)
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
validate_sshkey = RegexValidator(ssh_public_key_re,
    _(u"Enter a valid SSH public key with comment (SSH2 RSA or DSA)."), "invalid")


class CachedClusterObject(models.Model):
    """
    mixin class for objects that reside on the cluster but some portion is
    cached in the database.  This class contains logic and other structures for
    handling cache loading transparently
    """
    serialized_info = models.TextField(null=True, default=None, editable=False)
    mtime = PreciseDateTimeField(null=True, editable=False)
    cached = PreciseDateTimeField(null=True, editable=False)
    ignore_cache = models.BooleanField(default=False)
    
    __info = None
    error = None
    ctime = None

    def __init__(self, *args, **kwargs):
        super(CachedClusterObject, self).__init__(*args, **kwargs)
        self.load_info()

    @property
    def info(self):
        """
        Getter for self.info, a dictionary of data about a VirtualMachine.  This
        is a proxy to self.serialized_info that handles deserialization.
        Accessing this property will lazily deserialize info if it has not yet
        been deserialized.
        """
        if self.__info is None:
            if self.serialized_info is not None:
                self.__info = cPickle.loads(str(self.serialized_info))
        return self.__info

    @info.setter
    def info(self, value):
        """
        Setter for self.info, proxy to self.serialized_info that handles
        serialization.  When info is set, it will be parsed will trigger
        self._parse_info() to update persistent and non-persistent properties
        stored on the model instance.
        
        Calling this method will not force serialization.  Serialization of info
        is lazy and will only occur when saving.
        """
        self.__info = value
        self.parse_info()
        self.serialized_info = None

    def load_info(self):
        """
        Load cached info retrieved from the ganeti cluster.  This function
        includes a lazy cache mechanism that uses a timer to decide whether or
        not to refresh the cached information with new information from the
        ganeti cluster.
        
        This will ignore the cache when self.ignore_cache is True
        """
        if self.id:
            if self.ignore_cache:
                self.refresh()
            
            elif self.cached is None \
                or datetime.now() > self.cached+timedelta(0, 0, 0, settings.LAZY_CACHE_REFRESH):
                    self.refresh()
            else:
                if self.info:
                    self.parse_transient_info()
                else:
                    self.error = 'No Cached Info'

    def parse_info(self):
        """ Parse all values from the cached info """
        self.parse_transient_info()
        data = self.parse_persistent_info(self.info)
        for k in data:
            setattr(self, k, data[k])

    def refresh(self):
        """
        Retrieve and parse info from the ganeti cluster.  If successfully
        retrieved and parsed, this method will also call save().

        Failure while loading the remote class will result in an incomplete
        object.  The error will be stored to self.error
        """
        try:
            info_ = self._refresh()
            if info_:
                mtime = datetime.fromtimestamp(info_['mtime'])
                self.cached = datetime.now()
            else:
                # no info retrieved, use current mtime
                mtime = self.mtime
            
            if self.mtime is None or mtime > self.mtime:
                # there was an update. Set info and save the object
                self.info = info_
                self.check_job_status()
                self.save()
            else:
                # There was no change on the server.  Only update the cache
                # time. This bypasses the info serialization mechanism and
                # uses a smaller query.
                updates = self.check_job_status()
                if updates:
                    self.__class__.objects.filter(pk=self.id) \
                        .update(cached=self.cached, **updates)
                elif self.id is not None:
                    self.__class__.objects.filter(pk=self.id) \
                        .update(cached=self.cached)
                
        except GanetiApiError, e:
            self.error = str(e)
            GanetiError.objects.store_error(str(e), obj=self, code=e.code)

        else:
            self.error = None
            GanetiError.objects.clear_errors(obj=self)

    def _refresh(self):
        """
        Fetch raw data from the ganeti cluster.  This is specific to the object
        and must be implemented by it.
        """
        raise NotImplementedError

    def check_job_status(self):
        pass

    def parse_transient_info(self):
        """
        Parse properties from cached info that is stored on the class but not in
        the database.  These properties will be loaded every time the object is
        instantiated.  Properties stored on the class cannot be search
        efficiently via the django query api.

        This method is specific to the child object.
        """
        info_ = self.info
        # XXX ganeti 2.1 ctime is always None
        if info_['ctime'] is not None:
            self.ctime = datetime.fromtimestamp(info_['ctime'])

    @classmethod
    def parse_persistent_info(cls, info):
        """
        Parse properties from cached info that are stored in the database. These
        properties will be searchable by the django query api.

        This method is specific to the child object.
        """
        return {'mtime': datetime.fromtimestamp(info['mtime'])}

    def save(self, *args, **kwargs):
        """
        overridden to ensure info is serialized prior to save
        """
        if self.serialized_info is None:
            self.serialized_info = cPickle.dumps(self.__info)
        super(CachedClusterObject, self).save(*args, **kwargs)

    class Meta:
        abstract = True


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
    job_id = models.IntegerField(null=False)
    content_type = models.ForeignKey(ContentType, null=False)
    object_id = models.IntegerField(null=False)
    obj = GenericForeignKey('content_type', 'object_id')
    cluster = models.ForeignKey('Cluster', editable=False, related_name='jobs')
    cluster_hash = models.CharField(max_length=40, editable=False)
    
    cleared = models.BooleanField(default=False)
    finished = models.DateTimeField(null=True)
    status = models.CharField(max_length=10)
    
    objects = JobManager()
    
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
        if self.id and self.ignore_cache:
            self.info = self._refresh()
            self.save()
    
    @classmethod
    def parse_persistent_info(cls, info):
        """
        Parse status and turn off cache bypass flag if job has finished
        """
        data = {}
        data['status'] = info['status']
        if data['status'] in ('error','success'):
            data['ignore_cache'] = False
        if info['end_ts']:
            data['finished'] = cls.parse_end_timestamp(info)
        return data

    @classmethod
    def parse_end_timestamp(cls, info):
        sec, micro = info['end_ts']
        return datetime.fromtimestamp(sec+(micro/1000000.0))

    def parse_transient_info(self):
        pass
    
    def save(self, *args, **kwargs):
        """
        sets the cluster_hash for newly saved instances and writes the owner tag
        to ganeti
        """
        if self.id is None or self.cluster_hash == '':
            self.cluster_hash = self.cluster.hash
        
        super(Job, self).save(*args, **kwargs)

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
                break;
        return info['ops'][index]['OP_ID']


    def __repr__(self):
        return "<Job: '%s'>" % self.id
    
    def __str__(self):
        return repr(self)


class VirtualMachine(CachedClusterObject):
    """
    The VirtualMachine (VM) model represents VMs within a Ganeti cluster.  The
    majority of properties are a cache for data stored in the cluster.  All data
    retrieved via the RAPI is stored in VirtualMachine.info, and serialized
    automatically into VirtualMachine.serialized_info.

    Attributes that need to be searchable should be stored as model fields.  All
    other attributes will be stored within VirtualMachine.info.

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
    cluster = models.ForeignKey('Cluster', editable=False, default=0,
                                related_name='virtual_machines')
    hostname = models.CharField(max_length=128)
    owner = models.ForeignKey('ClusterUser', null=True, \
                              related_name='virtual_machines')
    virtual_cpus = models.IntegerField(default=-1)
    disk_size = models.IntegerField(default=-1)
    ram = models.IntegerField(default=-1)
    cluster_hash = models.CharField(max_length=40, editable=False)
    operating_system = models.CharField(max_length=128)
    status = models.CharField(max_length=10)
    
    # The last job reference indicates that there is at least one pending job
    # for this virtual machine.  There may be more than one job, and that can
    # never be prevented.  This just indicates that job(s) are pending and the
    # job related code should be run (status, cleanup, etc).
    last_job = models.ForeignKey(Job, null=True)
    
    # deleted flag indicates a VM is being deleted, but the job has not
    # completed yet.  VMs that have pending_delete are still displayed in lists
    # and counted in quotas, but only so status can be checked.
    pending_delete = models.BooleanField(default=False)
    deleted = False
    
    class Meta:
        ordering = ["hostname", ]
        unique_together = (("cluster", "hostname"),)

    @property
    def rapi(self):
        return get_rapi(self.cluster_hash, self.cluster_id)

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
        
        return data

    def check_job_status(self):
        """
        if the cache bypass is enabled then check the status of the last job
        when the job is complete we can reenable the cache.
        
        @returns - dictionary of values that were updates
        """
        if self.ignore_cache and self.last_job_id:
            (job_id,) = Job.objects.filter(pk=self.last_job_id)\
                            .values_list('job_id', flat=True)
            data = self.rapi.GetJobStatus(job_id)
            status = data['status']
            
            if status in ('success', 'error'):
                finished = Job.parse_end_timestamp(data)
                Job.objects.filter(pk=self.last_job_id) \
                    .update(status=status, ignore_cache=False, finished=finished)
                self.ignore_cache = False
            
            if status == 'success':
                self.last_job = None
                # if the job was a deletion, then delete this vm
                # XXX return a None to prevent refresh() from trying to update
                #     the cache setting for this VM
                # XXX delete may have multiple ops in it, but delete is always
                #     the last command run.
                if data['ops'][-1]['OP_ID'] == 'OP_INSTANCE_REMOVE':
                    self.delete()
                    self.deleted = True
                    return None
                
                return dict(ignore_cache=False, last_job=None)
            
            elif status == 'error':
                return dict(ignore_cache=False)

    def _refresh(self):
        # XXX if delete is pending then no need to refresh this object.
        if self.pending_delete:
            return None
        return self.rapi.GetInstance(self.hostname)

    def shutdown(self):
        id = self.rapi.ShutdownInstance(self.hostname)
        job = Job.objects.create(job_id=id, obj=self, cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def startup(self):
        id = self.rapi.StartupInstance(self.hostname)
        job = Job.objects.create(job_id=id, obj=self, cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def reboot(self):
        id = self.rapi.RebootInstance(self.hostname)
        job = Job.objects.create(job_id=id, obj=self, cluster_id=self.cluster_id)
        self.last_job = job
        VirtualMachine.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job

    def setup_vnc_forwarding(self, sport=''):
        password = ''
        info_ = self.info
        port = info_['network_port']
        node = info_['pnode']

        # use proxy for VNC connection
        if settings.VNC_PROXY:
            proxy_server = settings.VNC_PROXY.split(":")
            password = generate_random_password()
            result = request_forwarding(proxy_server, sport, node, port, password)
            if not result:
                return False, False, False
            else:
                return proxy_server[0], int(result), password

        else:
            return node, port, password

    def __repr__(self):
        return "<VirtualMachine: '%s'>" % self.hostname

    def __unicode__(self):
        return self.hostname


class Cluster(CachedClusterObject):
    """
    A Ganeti cluster that is being tracked by this manager tool
    """
    hostname = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    port = models.PositiveIntegerField(default=5080)
    description = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    hash = models.CharField(max_length=40, editable=False)

    # quota properties
    virtual_cpus = models.IntegerField(null=True, blank=True)
    disk = models.IntegerField(null=True, blank=True)
    ram = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["hostname", "description"]

    def __unicode__(self):
        return self.hostname

    def save(self, *args, **kwargs):
        self.hash = self.create_hash()
        super(Cluster, self).save(*args, **kwargs)

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
        return sha1('%s%s%s%s' % \
                    (self.username, self.password, self.hostname, self.port)) \
                .hexdigest()

    def get_quota(self, user=None):
        """
        Get the quota for a ClusterUser

        @return user's quota, default quota, or none
        """
        if user is None:
            return {'default':1, 'ram':self.ram, 'disk':self.disk, \
                    'virtual_cpus':self.virtual_cpus}
        
        # attempt to query user specific quota first.  if it does not exist then
        # fall back to the default quota
        query = Quota.objects.filter(cluster=self, user=user) \
                    .values('ram', 'disk', 'virtual_cpus')
        if len(query):
            (quota,) = query
            quota['default'] = 0
            return quota

        return {'default':1, 'ram':self.ram, 'disk':self.disk, \
                    'virtual_cpus':self.virtual_cpus, }

    def set_quota(self, user, values=None):
        """
        set the quota for a ClusterUser

        @param values: dictionary of values, or None to delete the quota
        """
        kwargs = {'cluster':self, 'user':user}
        if values is None:
            Quota.objects.filter(**kwargs).delete()
        else:
            quota, new = Quota.objects.get_or_create(**kwargs)
            quota.__dict__.update(values)
            quota.save()

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
            VirtualMachine(cluster=self, hostname=hostname).save()

        # deletes VMs that are no longer in ganeti
        if remove:
            missing_ganeti = filter(lambda x: str(x) not in ganeti, db)
            if missing_ganeti:
                self.virtual_machines \
                    .filter(hostname__in=missing_ganeti).delete()

    @property
    def missing_in_ganeti(self):
        """
        Returns list of VirtualMachines that are missing from the ganeti cluster
        but present in the database
        """
        ganeti = self.instances()
        db = self.virtual_machines.all().values_list('hostname', flat=True)
        return filter(lambda x: str(x) not in ganeti, db)

    @property
    def missing_in_db(self):
        """
        Returns list of VirtualMachines that are missing from the database, but
        present in ganeti
        """
        ganeti = self.instances()
        db = self.virtual_machines.all().values_list('hostname', flat=True)
        return filter(lambda x: unicode(x) not in db, ganeti)

    def _refresh(self):
        return self.rapi.GetInfo()

    def nodes(self, bulk=False):
        """Gets all Cluster Nodes

        Calls the rapi client for the nodes of the cluster.
        """
        try:
            return self.rapi.GetNodes(bulk=bulk)
        except GanetiApiError:
            return []

    def node(self, node):
        """Get a single Node
        Calls the rapi client for a specific cluster node.
        """
        try:
            return self.rapi.GetNode(node)
        except GanetiApiError:
            return None

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


class VirtualMachineTemplate(models.Model):
    """
    Virtual Machine Template holds all the values for the create virtual machine
      form so that they can automatically be used or edited by a user.
    """
    cluster = models.ForeignKey('Cluster')
    start = models.BooleanField(verbose_name='Start up After Creation', \
                default=True)
    name_check = models.BooleanField(verbose_name='DNS Name Check', \
                default=True)
    iallocator = models.BooleanField(verbose_name='Automatic Allocation', \
                default=False)
    iallocator_hostname = models.CharField(null=True, blank=True, \
                max_length=255)
    disk_template = models.CharField(max_length=16)
    pnode = models.CharField(verbose_name='Primary Node', max_length=255, \
                null=True, blank=True)
    snode = models.CharField(verbose_name='Secondary Node', max_length=255, \
                null=True, blank=True)
    os = models.CharField(verbose_name='Operating System', max_length=255)
    # BEPARAMS
    vcpus = models.IntegerField(verbose_name='Virtual CPUs', \
                validators=[MinValueValidator(1)])
    ram = models.IntegerField(verbose_name='Memory', \
                validators=[MinValueValidator(100)])
    disk_size = models.IntegerField(verbose_name='Disk Size', \
                validators=[MinValueValidator(100)])
    disk_type = models.CharField(verbose_name='Disk Type', max_length=255)
    nicmode = models.CharField(verbose_name='NIC Mode', max_length=255)
    niclink = models.CharField(verbose_name='NIC Link', max_length=255, \
                null=True, blank=True)
    nictype = models.CharField(verbose_name='NIC Type', max_length=255)
    # HVPARAMS
    kernelpath = models.CharField(verbose_name='Kernel Path', null=True, \
                blank=True, max_length=255)
    rootpath = models.CharField(verbose_name='Root Path', default='/', \
                max_length=255)
    serialconsole = models.BooleanField(verbose_name='Enable Serial Console')
    bootorder = models.CharField(verbose_name='Boot Device', max_length=255)
    imagepath = models.CharField(verbose_name='CD-ROM Image Path', null=True, \
                blank=True, max_length=512)

    def __unicode__(self):
        return self.templatename


if settings.TESTING:
    # XXX - if in debug mode create a model for testing cached cluster objects
    class TestModel(CachedClusterObject):
        """ simple implementation of a cached model that has been instrumented """
        cluster = models.ForeignKey(Cluster)
        saved = False
        data = {'mtime': 1285883187.8692000, 'ctime': 1285799513.4741000}
        throw_error = None
        
        def _refresh(self):
            if self.throw_error:
                raise self.throw_error
            return self.data

        def save(self, *args, **kwargs):
            self.saved = True
            super(TestModel, self).save(*args, **kwargs)


class GanetiErrorManager(models.Manager):

    def clear_error(self, id):
        """
        Clear one particular error (used in overview template).
        """
        return self.filter(pk=id).update(cleared=True)

    def clear_errors(self, *args, **kwargs):
        """
        Clear errors instead of deleting them.
        """
        return self.get_errors(cleared=False, *args, **kwargs) \
            .update(cleared=True)

    def remove_errors(self, *args, **kwargs):
        """
        Just shortcut if someone wants to remove some errors.
        """
        return self.get_errors(*args, **kwargs).delete()

    def get_errors(self, obj=None, **kwargs):
        """
        Manager method used for getting QuerySet of all errors depending on
        passed arguments.
        
        @param  obj   affected object (itself or just QuerySet)
        @param kwargs: additional kwargs for filtering GanetiErrors
        """
        if obj is None:
            return self.filter(**kwargs)
        
        # Create base query of errors to return.
        #
        # if it's a Cluster or a queryset for Clusters, then we need to get all
        # errors from the Clusters.  Do this by filtering on GanetiError.cluster
        # instead of obj_id.
        if isinstance(obj, (Cluster,)):
            return self.filter(cluster=obj, **kwargs)
        
        elif isinstance(obj, (QuerySet,)):
            if obj.model == Cluster:
                return self.filter(cluster__in=obj, **kwargs)
            else:
                ct = ContentType.objects.get_for_model(obj.model)
                return self.filter(obj_type=ct, obj_id__in=obj, **kwargs)
        
        else:
            ct = ContentType.objects.get_for_model(obj.__class__)
            return self.filter(obj_type=ct, obj_id=obj.pk, **kwargs)

    def store_error(self, msg, obj, code, **kwargs):
        """
        Manager method used to store errors

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
        # 404 can occur on any object, but when it occurs on a cluster, then any
        # of its children must not see the error again
        elif code == 404:
            if not is_cluster:
                # return if the error exists for cluster
                try:
                    c_ct = ContentType.objects.get_for_model(Cluster)
                    return self.get(msg=msg, obj_type=c_ct, code=code,
                            obj_id=obj.cluster_id, cleared=False)

                except GanetiError.DoesNotExist:
                    # we want to proceed when the error is not cluster-specific
                    pass

        # XXX use a try/except instead of get_or_create().  get_or_create()
        # does not allow us to set cluster_id.  This means we'd have to query
        # the cluster object to create the error.  we can't guaranteee the
        # cluster will already be queried so use create() instead which does
        # allow cluster_id
        try:
            return self.get(msg=msg, obj_type=ct, obj_id=obj.pk, code=code,
                            **kwargs)

        except GanetiError.DoesNotExist:
            cluster_id = obj.pk if is_cluster else obj.cluster_id

            return self.create(msg=msg, obj_type=ct, obj_id=obj.pk,
                               cluster_id=cluster_id, code=code, **kwargs)


class GanetiError(models.Model):
    """
    Class for storing errors which occured in Ganeti
    """
    cluster = models.ForeignKey(Cluster)
    msg = models.TextField()
    code = models.PositiveSmallIntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # determines if the errors still appears or not
    cleared = models.BooleanField(default=False)

    # cluster object (cluster, VM, Node) affected by the error (if any)
    obj_type = models.ForeignKey(ContentType, related_name="ganeti_errors")
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey("obj_type", "obj_id")

    objects = GanetiErrorManager()

    class Meta:
        ordering = ("-timestamp", "code", "msg")

    def __repr__(self):
        return "<GanetiError '%s'>" % (self.msg)

    def __unicode__(self):
        base = "[%s] %s" % (self.timestamp, self.msg)
        return base


class VirtualMachineTemplate(models.Model):
    """
    Virtual Machine Template holds all the values for the create virtual machine
      form so that they can automatically be used or edited by a user.
    """
    cluster = models.ForeignKey('Cluster')
    start = models.BooleanField(verbose_name='Start up After Creation', \
                default=True)
    name_check = models.BooleanField(verbose_name='DNS Name Check', \
                default=True)
    iallocator = models.BooleanField(verbose_name='Automatic Allocation', \
                default=False)
    iallocator_hostname = models.CharField(null=True, blank=True, \
                max_length=255)
    disk_template = models.CharField(max_length=16)
    pnode = models.CharField(verbose_name='Primary Node', max_length=255, \
                null=True, blank=True)
    snode = models.CharField(verbose_name='Secondary Node', max_length=255, \
                null=True, blank=True)
    os = models.CharField(verbose_name='Operating System', max_length=255)
    # BEPARAMS
    vcpus = models.IntegerField(verbose_name='Virtual CPUs', \
                validators=[MinValueValidator(1)])
    ram = models.IntegerField(verbose_name='Memory', \
                validators=[MinValueValidator(100)])
    disk_size = models.IntegerField(verbose_name='Disk Size', \
                validators=[MinValueValidator(100)])
    disk_type = models.CharField(verbose_name='Disk Type', max_length=255)
    nicmode = models.CharField(verbose_name='NIC Mode', max_length=255)
    niclink = models.CharField(verbose_name='NIC Link', max_length=255, \
                null=True, blank=True)
    nictype = models.CharField(verbose_name='NIC Type', max_length=255)
    # HVPARAMS
    kernelpath = models.CharField(verbose_name='Kernel Path', null=True, \
                blank=True, max_length=255)
    rootpath = models.CharField(verbose_name='Root Path', default='/', \
                max_length=255)
    serialconsole = models.BooleanField(verbose_name='Enable Serial Console')
    bootorder = models.CharField(verbose_name='Boot Device', max_length=255)
    imagepath = models.CharField(verbose_name='CD-ROM Image Path', null=True, \
                blank=True, max_length=512)

    def __unicode__(self):
        return self.templatename

class ClusterUser(models.Model):
    """
    Base class for objects that may interact with a Cluster or VirtualMachine.
    """
    #clusters = models.ManyToManyField(Cluster, through='Quota',
    #                                  related_name='users')
    name = models.CharField(max_length=128)
    real_type = models.ForeignKey(ContentType, editable=False, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(ClusterUser, self).save(*args, **kwargs)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    def __unicode__(self):
        return self.name

    def used_resources(self, cluster=None, only_running=False):
        """
        Return dictionary of total resources used by VMs that this ClusterUser
        has perms to.
        @param cluster  if set, get only VMs from specified cluster
        @param only_running  if set, get only running VMs
        """
        # XXX - order_by must be cleared or it breaks annotation grouping since
        #       the default order_by field is also added to the group_by clause
        base = self.virtual_machines.all().order_by()

        if only_running:
            base = base.filter(status="running")
        base = base.exclude(ram=-1, disk_size=-1, virtual_cpus=-1)
        
        if cluster:
            base = base.filter(cluster=cluster)
            result = base.aggregate(ram=Sum('ram'), disk=Sum('disk_size'), \
                                  virtual_cpus=Sum('virtual_cpus'))
            
            # repack with zeros instead of Nones
            if result['disk'] is None:
                result['disk'] = 0
            if result['ram'] is None:
                result['ram'] = 0
            if result['virtual_cpus'] is None:
                result['virtual_cpus'] = 0
            return result
        
        else:
            base = base.values('cluster').annotate(uram=Sum('ram'), \
                                            udisk=Sum('disk_size'), \
                                            uvirtual_cpus=Sum('virtual_cpus'))
            
            # repack as dictionary
            result = {}
            for used in base:
                # repack with zeros instead of Nones, change index names
                used['ram'] = 0 if not used['uram'] else used['uram']
                used['disk'] = 0 if not used['udisk'] else used['udisk']
                used['virtual_cpus'] = 0 if not used['uvirtual_cpus'] else used['uvirtual_cpus']
                used.pop("uvirtual_cpus")
                used.pop("udisk")
                used.pop("uram")
                result[used.pop('cluster')] = used
                
            return result


class Profile(ClusterUser):
    """
    Profile associated with a django.contrib.auth.User object.
    """
    user = models.OneToOneField(User)

    def grant(self, perm, object):
        self.user.grant(perm, object)

    def set_perms(self, perms, object):
        self.user.set_perms(perms, object)

    def get_objects_any_perms(self, *args, **kwargs):
        return self.user.get_objects_any_perms(*args, **kwargs)

    def has_perm(self, *args, **kwargs):
        return self.user.has_perm(*args, **kwargs)


class Organization(ClusterUser):
    """
    An organization is used for grouping Users.  Organizations are matched with
    an instance of contrib.auth.models.Group.  This model exists so that
    contrib.auth.models.Group have a 1:1 relation with a ClusterUser on which quotas and
    permissions can be assigned.
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


class Quota(models.Model):
    """
    A resource limit imposed on a ClusterUser for a given Cluster.  The
    attributes of this model represent maximum values the ClusterUser can
    consume.  The absence of a Quota indicates unlimited usage.
    """
    user = models.ForeignKey(ClusterUser, related_name='quotas')
    cluster = models.ForeignKey(Cluster, related_name='quotas')

    ram = models.IntegerField(default=0, null=True)
    disk = models.IntegerField(default=0, null=True)
    virtual_cpus = models.IntegerField(default=0, null=True)


class SSHKey(models.Model):
    """
    Model representing user's SSH public key. Virtual machines rely on
    many ssh keys.
    """
    key = models.TextField(validators=[validate_sshkey])
    #filename = models.CharField(max_length=128) # saves key file's name
    user = models.ForeignKey(User)


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
        # won't be available the first time syncdb is run.  Catch the error here
        # and let the south migration handle it.
        pass


def update_cluster_hash(sender, instance, **kwargs):
    """
    Updates the Cluster hash for all of it's VirtualMachines
    """
    instance.virtual_machines.all().update(cluster_hash=instance.hash)
    instance.jobs.all().update(cluster_hash=instance.hash)


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
post_syncdb.connect(management.update_sites_module, sender=sites_app, \
  dispatch_uid = "ganeti.management.update_sites_module")

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
        # won't be available the first time syncdb is run.  Catch the error here
        # and let the south migration handle it.
        pass

post_syncdb.connect(regenerate_cu_children)


def log_group_create(sender, editor, **kwargs):
    """ log group creation signal """
    log_action(editor, sender, 'created')

def log_group_edit(sender, editor, **kwargs):
    """ log group edit signal """
    log_action(editor, sender, 'edited')

op_signals.view_group_created.connect(log_group_create)
op_signals.view_group_edited.connect(log_group_edit)


# Register permissions on our models.
# These are part of the DB schema and should not be changed without serious
# forethought.
# You *must* syncdb after you change these.
register(permissions.CLUSTER_PARAMS, Cluster)
register(permissions.VIRTUAL_MACHINE_PARAMS, VirtualMachine)
