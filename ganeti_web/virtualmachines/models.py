from django.db import models


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
    cluster = models.ForeignKey('Cluster', related_name='virtual_machines',
                                editable=False, default=0)
    hostname = models.CharField(max_length=128, db_index=True)
    owner = models.ForeignKey('ClusterUser', related_name='virtual_machines',
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


class VirtualMachineTemplate(models.Model):
    """
    Virtual Machine Template holds all the values for the create virtual
    machine form so that they can automatically be used or edited by a user.
    """

    template_name = models.CharField(max_length=255, default="")
    temporary = BooleanField(verbose_name=_("Temporary"), default=False)
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
    minmem = models.IntegerField(verbose_name=_('Minimum Memory'),
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
        if self.temporary:
            return u'(temporary)'
        else:
            return self.template_name

    def set_name(self, name):
        """
        Set this template's name.

        If the name is blank, this template will become temporary and its name
        will be set to a unique timestamp.
        """

        if name:
            self.template_name = name
        else:
            # The template is temporary and will be removed by the VM when the
            # VM successfully comes into existence.
            self.temporary = True
            # Give it a temporary name. Something unique. This is the number
            # of microseconds since the epoch; I figure that it'll work out
            # alright.
            self.template_name = str(int(time.time() * (10 ** 6)))
