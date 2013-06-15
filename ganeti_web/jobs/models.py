from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from utils import get_rapi
from utils.client import GanetiApiError
from clusters.models import CachedClusterObject


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
    cluster = models.ForeignKey('clusters.Cluster', related_name='jobs',
                                editable=False)
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
            except GanetiApiError as e:
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
