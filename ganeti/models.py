import cPickle
from datetime import datetime, timedelta
from hashlib import sha1
from threading import Thread
import time

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models


from object_permissions.registration import register, get_users, get_groups
from object_permissions.signals import granted, revoked
from object_permissions.models import UserGroup, ObjectPermissionType
from util import client
from util.client import GanetiApiError


CURL = client.GenericCurlConfig()
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


class CachedClusterObject(models.Model):
    """
    mixin class for objects that reside on the cluster but some portion is
    cached in the database.  This class contains logic and other structures for
    handling cache loading transparently
    """
    serialized_info = models.TextField(null=True, default=None, editable=False)
    cached = models.DateTimeField(null=True, editable=False)
    __info = None
    error = None
    mtime = None
    ctime = None
    
    def __init__(self, *args, **kwargs):
        super(CachedClusterObject, self).__init__(*args, **kwargs)
        self.load_info()
    
    @property
    def info(self):
        """
        Getter for self.info, a dictionary of data about a VirtualMachine.  This
        is a proxy to self.serialized_info that handles deserialization.
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
        """
        self.__info = value
        self.serialized_info = cPickle.dumps(self.__info)
        self.parse_info()

    def load_info(self):
        """
        Load cached info retrieved from the ganeti cluster.  This function
        includes a lazy cache mechanism that uses a timer to decide whether or
        not to refresh the cached information with new information from the
        ganeti cluster.
        """
        if self.id:
            if self.cached is None \
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
        self.parse_persistent_info()

    def refresh(self):
        """
        Retrieve and parse info from the ganeti cluster.  If successfully
        retrieved and parsed, this method will also call save().
        
        Failure while loading the remote class will result in an incomplete
        object.  The error will be stored to self.error
        """
        try:
            self.info = self._refresh()
            self.parse_info()
            self.cached = datetime.now()
            self.save()
            self.error = None
        except GanetiApiError, e:
            self.error = str(e)

    def _refresh(self):
        """
        Fetch raw data from the ganeti cluster.  This is specific to the object
        and must be implemented by it.
        """
        raise NotImplementedError

    def parse_transient_info(self):
        """
        Parse properties from cached info that is stored on the class but not in
        the database.  These properties will be loaded every time the object is
        instantiated.  Properties stored on the class cannot be search
        efficiently via the django query api.  
        
        This method is specific to the child object.
        """
        info_ = self.info
        self.ctime = datetime.fromtimestamp(info_['ctime'])
        self.mtime = datetime.fromtimestamp(info_['mtime'])

    def parse_persistent_info(self):
        """
        Parse properties from cached info that are stored in the database. These
        properties will be searchable by the django query api.
        
        This method is specific to the child object.
        """
        pass

    class Meta:
        abstract = True


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
    cluster = models.ForeignKey('Cluster', editable=False,
                                related_name='virtual_machines')
    hostname = models.CharField(max_length=128)
    owner = models.ForeignKey('ClusterUser', null=True)
    virtual_cpus = models.IntegerField(default=-1)
    disk_size = models.IntegerField(default=-1)
    ram = models.IntegerField(default=-1)
    cluster_hash = models.CharField(max_length=40, editable=False)
    
    @property
    def rapi(self):
        return get_rapi(self.cluster_hash, self.cluster_id)

    def save(self, *args, **kwargs):
        """
        sets the cluster_hash for newly saved instances
        """
        if self.id is None:
            self.cluster_hash = self.cluster.hash
        super(VirtualMachine, self).save(*args, **kwargs)

    def parse_persistent_info(self):
        """
        Loads all values from cached info, included persistent properties that
        are stored in the database
        """
        info_ = self.info
        
        # Group permission tags by [group|user] & id.  Once they have been
        # parsed process the lists to set or delete all perms.  This ensures
        # that only a single query per user will be executed, plus 2 extra
        # queries to check for users and groups to remove all permissions from.
        tagged_users = {}
        tagged_groups = {}
        for tag in info_['tags']:
            if tag.startswith('GANETI_WEB_MANAGER:'):
                perm, group, id = tag[19:].split(':')
                group = True if group == 'G' else False
                if group:
                    perms = tagged_groups.get(id, [])
                    tagged_groups[id] = perms
                else:
                    perms = tagged_users.get(id, [])
                    tagged_users[id] = perms
                perms.append(perm)
        
        # set permissions for all uses with permissions
        for id in tagged_users:
            try:
                user = User.objects.get(id=id)
                user.set_perms(tagged_users[id], self)
            except (User.DoesNotExist, ObjectPermissionType.DoesNotExist):
                pass
        for id in tagged_groups:
            try:
                group = UserGroup.objects.get(id=id)
                group.set_perms(tagged_groups[id], self)
            except (UserGroup.DoesNotExist, ObjectPermissionType.DoesNotExist):
                pass
        
        # revoke all permissions for any user who had all permissions removed
        for user in get_users(self).exclude(id__in=tagged_users.keys()):
            user.revoke_all(self)
        for group in get_groups(self).exclude(id__in=tagged_groups.keys()):
            group.revoke_all(self)
        
        # Parse resource properties
        self.ram = self.info['beparams']['memory']
        self.virtual_cpus = self.info['beparams']['vcpus']
        # Sum up the size of each disk used by the VM
        disk_size = 0
        for disk in self.info['disk.sizes']:
            disk_size += disk
        self.disk_size = disk_size 

    def add_permission_tag(self, grantee, perm):
        """
        Adds a permission tag to this VirtualMachine
        """
        group = 'G' if isinstance(grantee, (UserGroup,)) else 'U'
        tag = 'GANETI_WEB_MANAGER:%s:%s:%s' % (perm, group, grantee.id)
        # TODO - implement pushing the tag to ganeti
    
    def remove_permission_tag(self, grantee, perm):
        """
        Removes a permission tag from this VirtualMachine
        """
        group = 'G' if isinstance(grantee, (UserGroup,)) else 'U'
        tag = 'GANETI_WEB_MANAGER:%s:%s:%s' % (perm, group, grantee.id)
        print 'Removing: ', tag
        # TODO - implement pushing the tag to ganeti
    
    def _refresh(self):
        return self.rapi.GetInstance(self.hostname)

    def shutdown(self):
        return self.rapi.ShutdownInstance(self.hostname)

    def startup(self):
        return self.rapi.StartupInstance(self.hostname)

    def reboot(self):
        return self.rapi.RebootInstance(self.hostname)

    def __repr__(self):
        return "<VirtualMachine: '%s'>" % self.hostname

    def __unicode__(self):
        return self.hostname


class Cluster(CachedClusterObject):
    """
    A Ganeti cluster that is being tracked by this manager tool
    """
    hostname = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=50)
    port = models.PositiveIntegerField(default=5080)
    description = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    hash = models.CharField(max_length=40, editable=False)
    
    # quota properties
    virtual_cpus = models.IntegerField(null=True, blank=True)
    disk = models.IntegerField(null=True, blank=True)
    ram = models.IntegerField(null=True, blank=True)
    
    def __unicode__(self):
        return self.hostname
    
    def save(self):
        self.hash = self.create_hash()
        super(Cluster, self).save()
    
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
        
        query = Quota.objects.filter(cluster=self, user=user)
        if query.exists():
            (quota,) = query.values('ram', 'disk', 'virtual_cpus')
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
    
    def sync_virtual_machines(self):
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
        missing_ganeti = filter(lambda x: str(x) not in ganeti, db)
        if missing_ganeti:
            self.virtual_machines.filter(hostname__in=missing_ganeti).delete()

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


class ClusterUser(models.Model):
    """
    Base class for objects that may interact with a Cluster or VirtualMachine.
    """
    clusters = models.ManyToManyField(Cluster, through='Quota',
                                      related_name='users')
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


class Profile(ClusterUser):
    """
    Profile associated with a django.contrib.auth.User object.
    """
    user = models.OneToOneField(User)
    
    def grant(self, perm, object):
        self.user.grant(perm, object)
    
    def set_perms(self, perms, object):
        self.user.set_perms(perms, object)


class Organization(ClusterUser):
    """
    An organization is used for grouping Users.  Organizations are matched with
    an instance of object_permission.UserGroup.  This model exists so that
    UserGroups have a 1:1 relation with a ClusterUser on which quotas and
    permissions can be assigned.
    """
    user_group = models.OneToOneField(UserGroup, related_name='organization')
    
    def grant(self, perm, object):
        self.user_group.grant(perm, object)

    def set_perms(self, perms, object):
        self.user_group.set_perms(perms, object)


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


def create_profile(sender, instance, **kwargs):
    """
    Create a profile object whenever a new user is created, also keeps the
    profile name synchronized with the username
    """
    profile, new = Profile.objects.get_or_create(user=instance)
    if profile.name != instance.username:
        profile.name = instance.username
        profile.save()


def update_cluster_hash(sender, instance, **kwargs):
    """
    Updates the Cluster hash for all of it's VirtualMachines
    """
    instance.virtual_machines.all().update(cluster_hash=instance.hash)


def update_organization(sender, instance, **kwargs):
    """
    Creates a Organizations whenever a object_permissions.UserGroup is created
    """
    org, new = Organization.objects.get_or_create(user_group=instance)
    org.name = instance.name
    org.save()


def add_virtual_machine_tag(sender, perm, object, **kwargs):
    """
    Pass through to virtual machine to add permission tag
    """
    if isinstance(object, (VirtualMachine,)):
        object.add_permission_tag(sender, perm)


def remove_virtual_machine_tag(sender, perm, object, **kwargs):
    """
    Pass through to virtual machine to remove permission tag
    """
    # XXX this does not appear to be called
    if isinstance(object, (VirtualMachine,)):
        object.remove_permission_tag(sender, perm)


models.signals.post_save.connect(create_profile, sender=User)
models.signals.post_save.connect(update_cluster_hash, sender=Cluster)
models.signals.post_save.connect(update_organization, sender=UserGroup)
register('admin', Cluster)
register('create_vm', Cluster)
register('admin', VirtualMachine)

granted.connect(add_virtual_machine_tag)
revoked.connect(add_virtual_machine_tag)