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
from datetime import datetime

from django.utils import simplejson
from twisted.internet import reactor
from twisted.internet.defer import DeferredList, Deferred
from twisted.web import client
from ganeti.cacher import Timer, Counter
from ganeti.models import Cluster, VirtualMachine


VMS_URL = 'https://%s:%s/2/instances?bulk=1'


class VirtualMachineCacheUpdater(object):

    def update(self):
        """
        Updates the cache for all all VirtualMachines in all clusters.  This method
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
        d = client.getPage(str(VMS_URL % (cluster.hostname, cluster.port)))
        d.addCallback(self.process_cluster_info, cluster, deferred.callback)
        return deferred
    
    def process_cluster_info(self, json, cluster, callback):
        """
        process data received from ganeti.
        """
        print '%s:' % cluster.hostname
        infos = simplejson.loads(json)
        self.timer.tick('info fetched from ganeti     ')
        updated = Counter()
        base = cluster.virtual_machines.all()
        mtimes = base.values_list('hostname', 'id', 'mtime', 'status')

        data = {}
        for name, id, mtime, status in mtimes:
            data[name] = (id, float(mtime) if mtime else None, status)
        self.timer.tick('mtimes fetched from db       ')

        deferreds = [self.update_vm(cluster, info, data, updated) for info in infos]
        deferred_list = DeferredList(deferreds)

        # batch update the cache updated time for all VMs in this cluster. This
        # will set the last updated time for both VMs that were modified and for
        # those that weren't.  even if it wasn't modified we want the last
        # updated time to be up to date.
        #
        # XXX don't bother checking to see whether this query needs to run.  It
        # normal usage it will almost always need to
        def update_timestamps(result):
            print '    updated: %s out of %s' % (updated, len(infos))
            base.update(cached=datetime.now())
            self.timer.tick('records or timestamps updated')
        deferred_list.addCallback(update_timestamps)

        # XXX it would be nice if the deferred list could be returned and this
        # callback hooked up outside of the method, but that doesn't seem
        # possible
        deferred_list.addCallback(callback)

    def update_vm(self, cluster, info, data, updated):
        """
        updates an individual VirtualMachine: this just sets up the work in a
        deferred by using callLater.  Actual work is done in _update_vm().

        @param cluster - cluster this node is on
        @param info - info from ganeti
        @param data - data from database
        @param updated - counter object
        @return Deferred chained to _update_node() call
        """
        deferred = Deferred()
        args = (cluster, info, data, updated, deferred.callback)
        reactor.callLater(0, self._update_vm, *args)
        return deferred

    def _update_vm(self, cluster, info, data, updated, callback):
        """
        updates an individual VirtualMachine, this is the actual work function

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
