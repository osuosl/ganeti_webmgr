
from django.db import models
from django.conf import settings

from clusters.models import CachedClusterObject
from jobs.models import Job

from ganeti_web import constants
from utils import generate_random_password, get_rapi
from utils.client import REPLACE_DISK_AUTO
from utils.fields import LowerCaseCharField
from vm_templates.models import VirtualMachineTemplate

if settings.CONSOLE_PROXY:
    from utils.vncdaemon.vapclient import request_forwarding, request_ssh


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

    XXX Serialized_info can possibly be changed to a CharField if an upper
        limit can be determined. (Later Date, if it will optimize db)

    """
    cluster = models.ForeignKey('clusters.Cluster',
                                related_name='virtual_machines',
                                editable=False, default=0)
    hostname = LowerCaseCharField(max_length=128, db_index=True)
    owner = models.ForeignKey('authentication.ClusterUser',
                              related_name='virtual_machines',
                              null=True, blank=True,
                              on_delete=models.SET_NULL)
    virtual_cpus = models.IntegerField(default=-1)
    disk_size = models.IntegerField(default=-1)
    ram = models.IntegerField(default=-1)
    minram = models.IntegerField(default=-1)
    cluster_hash = models.CharField(max_length=40, editable=False)
    operating_system = models.CharField(max_length=128)
    status = models.CharField(max_length=14)

    # node relations
    primary_node = models.ForeignKey('nodes.Node', related_name='primary_vms',
                                     null=True, blank=True)
    secondary_node = models.ForeignKey('nodes.Node',
                                       related_name='secondary_vms',
                                       null=True, blank=True)

    # The last job reference indicates that there is at least one pending job
    # for this virtual machine.  There may be more than one job, and that can
    # never be prevented.  This just indicates that job(s) are pending and the
    # job related code should be run (status, cleanup, etc).
    last_job = models.ForeignKey('jobs.Job', related_name="+", null=True,
                                 blank=True)

    # deleted flag indicates a VM is being deleted, but the job has not
    # completed yet.  VMs that have pending_delete are still displayed in lists
    # and counted in quotas, but only so status can be checked.
    pending_delete = models.BooleanField(default=False)
    deleted = False

    # Template temporarily stores parameters used to create this virtual
    # machine. This template is used to recreate the values entered into the
    # form.
    template = models.ForeignKey("vm_templates.VirtualMachineTemplate",
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
        from nodes.models import Node
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
        password = ''
        info_ = self.info
        port = info_['network_port']
        node = info_['pnode']

        if settings.CONSOLE_PROXY:
            proxy_server = settings.CONSOLE_PROXY.split(":")
            password = generate_random_password()
            sport = request_ssh(proxy_server, sport, node, port,
                                password, command)

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
        if settings.CONSOLE_PROXY:
            proxy_server = settings.CONSOLE_PROXY.split(":")
            password = generate_random_password()
            result = request_forwarding(proxy_server, node, port, password,
                                        sport=sport, tls=tls)
            if result:
                return proxy_server[0], int(result), password
        else:
            return node, port, password

    def __repr__(self):
        return "<VirtualMachine: '%s'>" % self.hostname
