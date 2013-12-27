import binascii
import re
import cPickle
from datetime import datetime, timedelta
from hashlib import sha1

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from utils import get_rapi
from utils.fields import (
    PatchedEncryptedCharField, PreciseDateTimeField, LowerCaseCharField
)
from utils.client import GanetiApiError
from utils.models import Quota



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
        from utils.models import GanetiError

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

        except GanetiApiError as e:
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
                self.error = msg
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
        # preventing circular import
        from jobs.models import Job

        if not self.last_job_id:
            return {}

        ct = ContentType.objects.get_for_model(self)
        qs = Job.objects.filter(content_type=ct, object_id=self.pk)
        jobs = qs.order_by("job_id")

        updates = {}
        status = 'unknown'
        op = None

        for job in jobs:
            try:
                data = self.rapi.GetJobStatus(job.job_id)

                if Job.valid_job(data):
                    op = Job.parse_op(data)
                    status = data['status']

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
        if not jobs or status in ('success', 'error', 'unknown'):
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


class Cluster(CachedClusterObject):
    """
    A Ganeti cluster that is being tracked by this manager tool
    """
    hostname = LowerCaseCharField(_('hostname'), max_length=128, unique=True)
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
    last_job = models.ForeignKey('jobs.Job', related_name='cluster_last_job',
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
        # preventing circular imports
        from virtualmachines.models import VirtualMachine

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

        # Get up to date data on all VMs
        self.refresh_virtual_machines()

    def refresh_virtual_machines(self):
        for vm in self.virtual_machines.all():
            vm.refresh()

    def sync_nodes(self, remove=False):
        """
        Synchronizes the Nodes in the database with the information
        this ganeti cluster has:
            * Nodes no longer in ganeti are deleted
            * Nodes missing from the database are added
        """
        # to prevent circular imports
        from nodes.models import Node

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

        # Get up to date data for all Nodes
        self.refresh_nodes()

    def refresh_nodes(self):
        for node in self.nodes.all():
            node.refresh()

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
        # preventing circular import
        from jobs.models import Job

        # no exception handling, because it's being done in a view
        id = self.rapi.RedistributeConfig()
        job = Job.objects.create(job_id=id, obj=self, cluster_id=self.id)
        self.last_job = job
        Cluster.objects.filter(pk=self.id) \
            .update(last_job=job, ignore_cache=True)
        return job
