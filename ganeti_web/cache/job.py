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
from django.utils import simplejson as json

from twisted.internet import reactor
from twisted.internet.defer import DeferredList, Deferred
from twisted.web import client
from ganeti_web.cacher import Timer, Counter
from ganeti_web.models import Cluster, VirtualMachine, Job


JOBS_URL = 'https://%s:%s/2/jobs'
JOB_URL = 'https://%s/%s/2/jobs/%s'
COMPLETE_STATUS = ('success', 'error')

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
        print '%s:' % cluster.hostname
        ids = set(json.loads(info))
        self.timer.tick('info fetched from ganeti     ')
        updated = Counter()

        # fetch list of jobs in the cluster that are not yet finished.  if the
        # job is already finished then we don't need to update it
        db_ids = cluster.jobs \
                            .exclude(status__in=COMPLETE_STATUS) \
                            .values_list('job_id', flat=True)

        # update all running jobs
        # XXX this could be a choke point if there are many running jobs.  each
        # job will be a separate ganeti query
        deferreds = [self.update_job(id) for id in db_ids]
        ids -= set(db_ids)
        
        # get list of jobs that are finished.  use this to filter the list of
        # ids further
        # XXX this could be a joke point if there are a lot of IDs that are have
        # completed but have not yet been archived by ganeti.
        db_ids = cluster.jobs \
                            .filter(id__in=ids, status__in=COMPLETE_STATUS) \
                            .values_list('job_id', flat=True)
        ids -= set(db_ids)
        
        # any job id still left in the list is a new job.  Create the job and
        # associate it with the object it relates to
        for id in ids:
            deferreds.append(self.import_job(id))

        # XXX it would be nice if the deferred list could be returned and this
        # callback hooked up outside of the method, but that doesn't seem
        # possible
        deferred_list = DeferredList(deferreds)
        deferred_list.addCallback(callback)

    def get_job(self, cluster, id, updated):
        """ gets a job """
        deferred = Deferred()
        d = client.getPage(str(JOB_URL % (cluster.hostname, cluster.port, id)))
        d.addCallback(self.update_job, cluster, updated, deferred.callback)
        return deferred

    def update_job(self, cluster, id, updated, callback):
        """
        updates an individual Job: this just sets up the work in a
        deferred by using callLater.  Actual work is done in _update_job().

        @param cluster - cluster this node is on
        @param info - info from ganeti
        @param data - data from database
        @param updated - counter object
        @return Deferred chained to _update_node() call
        """
        deferred = Deferred()
        args = (cluster, id, updated, deferred.callback)
        reactor.callLater(0, self._update_job, *args)
        return deferred

    def _update_job(self, cluster, info, data, updated, callback):
        """
        updates an individual Job, this is the actual work function

        @param cluster - cluster this node is on
        @param info - info from ganeti
        @param data - data from database
        @param updated - counter object
        @param callback - callback fired when method is complete.
        """
        name = info['name']
        if name in data:
            id, mtime, status = data[name]
            if not mtime or mtime < info['mtime'] \
            or status != info['status']:
                print '    Virtual Machine (updated) : %s' % name
                #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
                # only update the whole object if it is new or modified.
                #
                # XXX status changes will not always be reflected in mtime
                # explicitly check status to see if it has changed.  failing
                # to check this would result in state changes being lost
                parsed = VirtualMachine.parse_persistent_info(info)
                VirtualMachine.objects.filter(pk=id) \
                    .update(serialized_info=cPickle.dumps(info), **parsed)
                updated += 1
        else:
            # new vm
            vm = VirtualMachine(cluster=cluster, hostname=info['name'])
            vm.info = info
            vm.save()

        callback(id)

    def complete(self, result):
        """ callback fired when everything is complete """
        self.timer.stop()
