from django.db import models
from django.db.models import Sum, Q

from clusters.models import CachedClusterObject
from virtualmachines.models import VirtualMachine
from jobs.models import Job

from ganeti_web import constants
from utils import get_rapi
from utils.fields import LowerCaseCharField


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

    cluster = models.ForeignKey('clusters.Cluster', related_name='nodes')
    hostname = LowerCaseCharField(max_length=128, unique=True)
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
    last_job = models.ForeignKey('jobs.Job', related_name="+", null=True,
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
        values = (VirtualMachine.objects
                  .filter(Q(primary_node=self) | Q(secondary_node=self))
                  .filter(status='running')
                  .exclude(ram=-1).order_by()
                  .aggregate(used=Sum('ram')))

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

    def natural_key(self):
        return self.hostname
