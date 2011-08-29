# Copyright (C) 2010 Oregon State University et al.
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

# Per #6579, do not change this import without discussion.
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson as json

from twisted.internet.defer import DeferredList, Deferred
from twisted.web import client
from ganeti_web.cache import Timer, Counter
from ganeti_web.models import Cluster, Node, VirtualMachine, Job


JOBS_URL = 'https://%s:%s/2/jobs'
JOB_URL = 'https://%s:%s/2/jobs/%s'
COMPLETE_STATUS = ('success', 'error', 'unknown')
IMPORTABLE_JOBS = {
    'OP_CLUSTER_REDIST_CONF':[Cluster, 'cluster_name'],
    'OP_NODE_MIGRATE':[Node, 'node_name'],
    'OP_INSTANCE_ADD':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_ADD_MDDRBD':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_FAILOVER':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_GROW_DISK':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_MIGRATE':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_MODIFY':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_MOVE':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_REBOOT':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_RECREATE_DISKS':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_REMOVE':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_REMOVE_MDDRBD':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_RENAME':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_REPLACE_DISKS':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_START':[VirtualMachine, 'instance_name'],
    'OP_INSTANCE_SHUTDOWN':[VirtualMachine, 'instance_name'],
}

# excluded op codes.
# 'OP_CLUSTER_POST_INIT':
# 'OP_CLUSTER_DESTROY'
# 'OP_CLUSTER_QUERY'
# 'OP_CLUSTER_VERIFY'
# 'OP_CLUSTER_VERIFY_DISKS'
# 'OP_CLUSTER_REPAIR_DISK_SIZES'
# 'OP_CLUSTER_CONFIG_QUERY'
# 'OP_CLUSTER_RENAME'
# 'OP_CLUSTER_SET_PARAMS'
# 'OP_NODE_REMOVE'
# 'OP_NODE_ADD'
# 'OP_NODE_QUERY'
# 'OP_NODE_QUERYVOLS'
# 'OP_NODE_QUERY_STORAGE'
# 'OP_NODE_MODIFY_STORAGE'
# 'OP_NODE_SET_PARAMS'
# 'OP_NODE_POWERCYCLE'
# 'OP_NODE_EVAC_STRATEGY'
# 'OP_TAGS_SET'
# 'OP_TAGS_DEL'

class JobCacheUpdater(object):

    def update_sync(self):
        """
        TODO: make this into an async method.  this method is just a test to see
        if an efficient update algorithm is possible

        1) query job ids from cluster

        Running Jobs:
        2) create base query of jobs with those ids
        3) filter jobs based on those not yet finished
        4) query running jobs individually, updating the job and related object as needed
        5) remove id from list

        New Jobs:
        6) any job leftover in the list is not yet in the database
        """
        #for cluster in Cluster.objects.all()
        pass

    def update(self):
        """
        Updates the cache for all all Jobs in all clusters.  This method
        processes the data in bulk, where possible, to reduce runtime.  Generally
        this should be faster than refreshing individual VirtualMachines.
        """
        self.timer = Timer()
        print '------[cache update]-------------------------------'
        clusters = Cluster.objects.all()
        deferreds = [self.get_cluster_info(cluster) for cluster in clusters]
        deferred_list = DeferredList(deferreds)
        deferred_list.addCallback(self.complete)
        return deferred_list

    def get_cluster_info(self, cluster):
        """
        fetch cluster info from ganeti
        """
        deferred = Deferred()
        d = client.getPage(str(JOBS_URL % (cluster.hostname, cluster.port)))
        d.addCallback(self.process_cluster_info, cluster, deferred.callback)
        return deferred

    def process_cluster_info(self, info, cluster, callback):
        """
        process data received from ganeti.
        """
        # parse json and repackage ids as a list
        ids = set((int(d['id']) for d in json.loads(info)))

        self.timer.tick('info fetched from ganeti     ')
        updated = Counter()

        # fetch list of jobs in the cluster that are not yet finished.  if the
        # job is already finished then we don't need to update it
        db_ids = set(cluster.jobs \
                            .exclude(status__in=COMPLETE_STATUS) \
                            .values_list('job_id', flat=True))

        # update all running jobs and archive any that aren't found
        # XXX this could be a choke point if there are many running jobs.  each
        # job will be a separate ganeti query
        current = db_ids & ids
        archived = db_ids - ids
        deferreds = [self.update_job(cluster, id, updated) for id in current]
        ids -= current

        # get list of jobs that are finished.  use this to filter the list of
        # ids further
        # XXX this could be a joke point if there are a lot of IDs that are have
        # completed but have not yet been archived by ganeti.
        db_ids = cluster.jobs \
                            .filter(job_id__in=ids, status__in=COMPLETE_STATUS) \
                            .values_list('job_id', flat=True)
        ids -= set(db_ids)

        # any job id still left in the list is a new job.  Create the job and
        # associate it with the object it relates to
        for id in ids:
            deferreds.append(self.import_job(cluster, id, updated))

        # archive any jobs that we do not yet have a complete status for but
        # were not found in list of jobs returned by ganeti
        if archived:
            self.archive_jobs(cluster, archived, updated)

        # XXX it would be nice if the deferred list could be returned and this
        # callback hooked up outside of the method, but that doesn't seem
        # possible
        deferred_list = DeferredList(deferreds)
        deferred_list.addCallback(callback)

    def archive_jobs(self, cluster, archived, updated):
        """
        updates a job that has been archived
        """
        updated += len(archived)
        # XXX clear all archived jobs
        Job.objects.filter(cluster=cluster, job_id__in=archived) \
            .update(ignore_cache=True, status='unknown')

        # XXX load all related objects to trigger their specific cleanup code.
        len(VirtualMachine.objects.filter(cluster=cluster, last_job_id__in=archived))
        len(Node.objects.filter(cluster=cluster, last_job_id__in=archived))
        len(Cluster.objects.filter(cluster=cluster, last_job_id__in=archived))

    def update_job(self, cluster, id, updated):
        """
        updates an individual Job

        @param cluster - cluster this node is on
        @param updated - counter object
        @return Deferred chained to _update_job() call
        """
        deferred = Deferred()
        d = client.getPage(str(JOB_URL % (cluster.hostname, cluster.port, id)))
        d.addCallback(self._update_job, cluster, id, updated, deferred.callback)
        d.addErrback(self._update_error, deferred.callback)
        return deferred

    def _update_error(self, error, callback):
        print 'Error updating: %s' % error
        callback(-1)
        

    def _update_job(self, info, cluster, id, updated, callback):
        """
        updates an individual Job, this is the actual work function.  Jobs that
        have a complete state (success or error) are updated.  All other jobs
        are ignored since job state is never cached.

        @param info - info from ganeti
        @param cluster - cluster this job is on
        @param id - job_id for job
        @param updated - counter object
        @param callback - callback fired when method is complete.
        """
        info = json.loads(info)
        if info['status'] in COMPLETE_STATUS:
            parsed = Job.parse_persistent_info(info)
            Job.objects.filter(job_id=id).update(
                serialized_info=cPickle.dumps(info), **parsed)

            # get related model and query the object.  Loading it will trigger
            # any logic in check_job_status
            op = info['ops'][0]
            model, hostname_key = IMPORTABLE_JOBS[op['OP_ID']]
            hostname = op[hostname_key]

            if isinstance(model, Cluster):
                base = model.objects.filter(hostname=hostname)
            else:
                base = model.objects.filter(cluster=cluster, hostname=hostname)
            updates = model._complete_job(cluster.id, hostname, op, info['status'])
            if updates:
                base.update(**updates)

            updated += 1
        callback(id)

    def import_job(self, cluster, id, updated):
        """
        import an individual Job

        @param cluster - cluster this job is on
        @param id - job_id of job
        @param updated - counter object
        @return Deferred chained to _import_job() call
        """
        deferred = Deferred()
        d = client.getPage(str(JOB_URL % (cluster.hostname, cluster.port, id)))
        d.addCallback(self._import_job, cluster, id, updated, deferred.callback)
        d.addErrback(self._update_error, deferred.callback)
        return deferred

    def _import_job(self, info, cluster, id, updated, callback):
        """
        import an individual Job, this is the actual work function.  Jobs that
        have a complete state (success or error) are updated.  All other jobs
        are ignored since job state is never cached.

        @param info - info from ganeti
        @param cluster - cluster this job is on
        @param id - job_id for job
        @param updated - counter object
        @param callback - callback fired when method is complete.
        """

        info = json.loads(info)
        if any((op['OP_ID'] in IMPORTABLE_JOBS for op in info['ops'])):
            # get related mode and object
            op = info['ops'][0]
            model, hostname_key = IMPORTABLE_JOBS[op['OP_ID']]
            hostname = op[hostname_key]
            base = model.objects.filter(hostname=hostname)
            if not isinstance(base, Cluster):
                base = base.filter(cluster=cluster)
            (obj_id,) = base.values_list('pk', flat=True)
            ct = ContentType.objects.get_for_model(model)

            # create job
            job = Job(cluster=cluster, job_id=id, content_type=ct, object_id=obj_id)
            job.cleared = info['status'] in COMPLETE_STATUS
            job.info = info
            job.save()
            updated += 1
        callback(id)
    
    def complete(self, result):
        """ callback fired when everything is complete """
        self.timer.stop()
