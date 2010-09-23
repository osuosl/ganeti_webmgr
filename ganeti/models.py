import cPickle

from django.db import models
from django.contrib.auth.models import User, Group
from ganeti_webmgr.util import client
from datetime import datetime

curl = client.GenericCurlConfig()

class VirtualMachine(models.Model):
    """
    The VirtualMachine (VM) model represents VMs within a Ganeti cluster.  The
    majority of properties are a cache for data stored in the cluster.  All data
    retrieved via the RAPI is stored in VirtualMachine.info, and serialized
    automatically into VirtualMachine.serialized_info.
    
    Attributes that need to be searchable should be stored.
    
    XXX Serialized_info can possibly be changed to a CharField if an upper
        limit can be determined. (Later Date, if it will optimize db)
    
    """
    cluster = models.ForeignKey('Cluster', editable=False,
                                related_name='virtual_machines')
    hostname = models.CharField(max_length=128, editable=False)
    owner = models.ForeignKey('ClusterUser', null=True)
    serialized_info = models.TextField(editable=False)
    virtual_cpus = models.IntegerField()
    disk_size = models.IntegerField()
    ram = models.IntegerField()
    
    ctime = None
    mtime = None
    __info = None

    def __init__(self, *args, **kwargs):
        super(VirtualMachine, self).__init__(*args, **kwargs)
        
        #TODO for now always update on init, this will be replaced with cache
        #    timeout later on.
        assert(self.cluster)
        
        if True:
            self.refresh()
        else:
            self._load_info()

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
        self._parse_info()

    @property
    def rapi(self):
        return self.cluster.rapi

    def refresh(self):
        """
        Refreshes info from the ganeti cluster.  Calling this method will also
        trigger self._parse_info() to update persistent and non-persistent
        properties stored on the model instance.
        """
        try:
            self.info = self.rapi.GetInstance(self.hostname)
            self._parse_info()
            self.save()
        except client.GanetiApiError:
            pass

    def _load_info(self):
        """
        Loads non-persistent properties from cached info
        """
        if getattr(self, 'ctime', None):
            self.ctime = datetime.fromtimestamp(self.info.ctime)
        if getattr(self, 'mtime', None):
            self.mtime = datetime.fromtimestamp(self.info.mtime)
        self.ram = self.info['beparams']['memory']
        self.virtual_cpus = self.info['beparams']['vcpus']
        # Sum up the size of each disk used by the VM
        disk_size = 0
        for disk in self.info['disk.sizes']:
            disk_size += disk
        self.disk_size = disk_size

    def _parse_info(self):
        """
        Loads all values from cached info, included values that are stored in
        the database
        """
        self._load_info()
        info_ = self.info
        '''
        XXX no tags yet.  not sure what the property name is called.
        for tag in info_['tags']:
            if tag.startswith('owner:'):
                try:
                    self.owner = ClusterUser.objects.get(name__iexact=tag.replace('owner:',''))
                except:
                    pass
        '''
        
        # TODO: load resource information    

    def shutdown(self):
        return self.clusterrapi.ShutdownInstance(self.hostname)

    def startup(self):
        return self.cluster.rapi.StartupInstance(self.hostname)

    def reboot(self):
        return self.cluster.rapi.RebootInstance(self.hostname)

    def __repr__(self):
        return "<VirtualMachine: '%s'>" % self.hostname

    def __unicode__(self):
        return self.hostname


class Cluster(models.Model):
    """
    A Ganeti cluster that is being tracked by this manager tool
    """
    hostname = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=50)
    port = models.PositiveIntegerField(default=5080)
    description = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)

    __rapi = None
    __rapi_config = None
    
    def __init__(self, *args, **kwargs):
        super(Cluster, self).__init__(*args, **kwargs)
        
        #XXX hostname wont be set for new instances
        if self.hostname:
            self._info = self.info()
            self.__dict__.update(self._info)
    
    @property
    def rapi(self):
        """
        retrieves the rapi client for this cluster.  The
        """
        if self.__rapi is None or self.__rapi_config != (self.hostname,):
            self.__rapi_config = (self.hostname,)
            self.__rapi = client.GanetiRapiClient(self.hostname,
                                                          curl_config_fn=curl)
        return self.__rapi

    def __unicode__(self):
        return self.hostname

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
        self.virtual_machines.filter(hostname__in=missing_ganeti).delete()

    def info(self):
        info = self.rapi.GetInfo()
        #print info['ctime']
        if 'ctime' in info and info['ctime']:
            info['ctime'] = datetime.fromtimestamp(info['ctime'])
        if 'mtime' in info and info['mtime']:
            info['mtime'] = datetime.fromtimestamp(info['mtime'])
        return info

    def nodes(self):
        """Gets all Cluster Nodes
        
        Calls the rapi client for the nodes of the cluster.
        """        
        return self.rapi.GetNodes()

    def node(self, node):
        """Get a single Node
        Calls the rapi client for a specific cluster node.
        """
        return self.rapi.GetNode(node)

    def instances(self):
        """Gets all VMs which reside under the Cluster
        Calls the rapi client for all instances.
        """
        return self.rapi.GetInstances()

    def instance(self, instance):
        """Get a single Instance
        Calls the rapi client for a specific instance.
        """
        return self.rapi.GetInstance(instance)


class ClusterUser(models.Model):
    """
    Base class for objects that may interact with a Cluster or VirtualMachine.
    """
    clusters = models.ManyToManyField(Cluster, through='Quota',
                                      related_name='users')
    name = models.CharField(max_length=128)
    
    class Meta:
        abstract = False

    def __unicode__(self):
        return self.name


class Profile(ClusterUser):
    """
    Profile associated with a django.contrib.auth.User object.
    """
    user = models.OneToOneField(User)


class Organization(ClusterUser):
    """
    An organization is used for grouping Users.  Organizations are intended for
    use when a Cluster or VirtualMachine is owned or managed by multiple people.
    """
    users = models.ManyToManyField(Profile, related_name="organizations",
                                   null=True, blank=True)


class Quota(models.Model):
    """
    A resource limit imposed on a ClusterUser for a given Cluster.  The
    attributes of this model represent maximum values the ClusterUser can
    consume.  The absence of a Quota indicates unlimited usage.
    """
    user = models.ForeignKey(ClusterUser, related_name='quotas')
    cluster = models.ForeignKey(Cluster, related_name='quotas')
    
    ram = models.IntegerField(default=0, null=True)
    disk_space = models.IntegerField(default=0, null=True)
    virtual_cpus = models.IntegerField(default=0, null=True)
    
    def __unicode__(self):
        return ''