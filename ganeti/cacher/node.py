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

from datetime import datetime
import cPickle

from twisted.internet.defer import DeferredList, Deferred
from twisted.internet import reactor
from twisted.web import client
from django.utils import simplejson

from ganeti.models import Cluster, Node, VirtualMachine


NODES_URL = 'https://%s:%s/2/nodes?bulk=1'


class Timer():

    def __init__(self, start=True):
        self.start()
        self.ticks = []

    def start(self):
        self.start = datetime.now()
        self.ticks = []
        self.last_tick = self.start

    def stop(self):
        self.end = datetime.now()
        print '    Total time: %s' %  (self.end - self.start)

    def tick(self, msg=''):
        now = datetime.now()
        duration = now-self.last_tick
        print '    %s : %s' % (msg, duration)
        self.last_tick = now
        self.ticks.append(duration.seconds + duration.microseconds/1000000.0)


class Counter(object):
    """ simpler counter class """

    def __init__(self):
        self.value = 0

    def __iadd__(self, other):
        self.value += other

    def __repr__(self):
        return str(self.value)


class NodeCacheUpdater(object):

    def _update_node(self, cluster, info, data, updated, callback):
        """
        updates an individual node, this is the actual work function

        @param cluster - cluster this node is on
        @param info - info from ganeti
        @param data - data from database
        @param updated - counter object
        @param callback - callback fired when method is complete.
        """
        hostname = info['name']
        if hostname in data:
            id, mtime = data[hostname]
            if not mtime or mtime < info['mtime']:
                print '    Node (updated) : %s' % hostname
                #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
                # only update the whole object if it is new or modified.
                parsed = Node.parse_persistent_info(info)
                Node.objects.filter(pk=id) \
                    .update(serialized_info=cPickle.dumps(info), **parsed)
                updated += 1
        else:
            # new node
            node = Node(cluster=cluster, hostname=info['name'])
            node.info = info
            node.save()
            id = node.pk


        # Updates relationships between a Node and its Primary and Secondary
        # VirtualMachines.  This always runs even when there are no updates but
        # it should execute quickly since it runs against an indexed column
        #
        # XXX this blocks so it may be worthwhile to spin this off into a
        # deferred just to break up this method.  
        VirtualMachine.objects \
            .filter(hostname__in=info['pinst_list']) \
            .update(primary_node=id)

        VirtualMachine.objects \
            .filter(hostname__in=info['sinst_list']) \
            .update(secondary_node=id)

        callback(id)

    def update_node(self, cluster, info, data, updated):
        """
        updates an individual node: this just sets up the work in a deferred
        by using callLater.  Actual work is done in _update_node().

        This will also chain update_related_vms

        @param cluster - cluster this node is on
        @param info - info from ganeti
        @param data - data from database
        @param updated - counter object
        @return Deferred chained to _update_node() call
        """
        deferred = Deferred()
        args = (cluster, info, data, updated, deferred.callback)
        reactor.callLater(0, self._update_node, *args)
        return deferred

    def get_cluster_info(self, cluster):
        """
        fetch cluster info from
        """
        deferred = Deferred()
        d = client.getPage(str(NODES_URL % (cluster.hostname, cluster.port)))
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
        base = cluster.nodes.all()
        mtimes = base.values_list('hostname', 'id', 'mtime')

        data = {}
        for hostname, id, mtime in mtimes:
            data[hostname] = (id, float(mtime) if mtime else None)
        self.timer.tick('mtimes fetched from db       ')

        deferreds = [self.update_node(cluster, info, data, updated) for info in infos]
        deferred_list = DeferredList(deferreds)

        # batch update the cache updated time for all Nodes in this cluster. This
        # will set the last updated time for both Nodes that were modified and for
        # those that weren't.  even if it wasn't modified we want the last
        # updated time to be up to date.
        #
        # XXX don't bother checking to see whether this query needs to run.  With
        # normal usage it will almost always need to
        def update_timestamps(result):
            print '    updated: %s out of %s' % (updated, len(infos))
            base.update(cached=datetime.now())
            self.timer.tick('records or timestamps updated')
        deferred_list.addCallback(update_timestamps)
        deferred_list.addCallback(callback)
        
        return deferred_list

    def update_cache(self):
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

    def complete(self, result):
        self.timer.stop()