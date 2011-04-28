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
import os
import sys
from threading import Thread
import time

import cPickle

# ==========================================================
# Setup django environment
# ==========================================================
if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    sys.path.insert(0, os.getcwd())
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db import transaction

from django.conf import settings
from ganeti.models import Cluster, Node, VirtualMachine


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


class NodeCacheUpdater(object):

    def _update_cluster(self, cluster):
        """
        updates nodes for an individual cluster
        """
        print '%s:' % cluster.hostname
        base = cluster.nodes.all()
        infos = cluster.rapi.GetNodes(bulk=True)
        self.timer.tick('info fetched from ganeti     ')
        updated = 0

        mtimes = base.values_list('hostname', 'id', 'mtime')
        d = {}
        for hostname, id, mtime in mtimes:
            d[hostname] = (id, float(mtime) if mtime else None)
        self.timer.tick('mtimes fetched from db       ')

        for info in infos:
            #print info
            hostname = info['name']

            if hostname in d:
                id, mtime = d[hostname]
                if not mtime or mtime < info['mtime']:
                    #print '    Node (updated) : %s' % hostname
                    #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
                    # only update the whole object if it is new or modified.
                    data = Node.parse_persistent_info(info)
                    Node.objects.filter(pk=id) \
                        .update(serialized_info=cPickle.dumps(info), **data)
                    updated += 1
            else:
                # new node
                node = Node(cluster=cluster, hostname=info['name'])
                node.info = info
                node.save()
                id = node.pk

            # set primary and secondary nodes.  This always executes but it
            # should be a fast query since it is indexed
            VirtualMachine.objects \
                .filter(hostname__in=info['pinst_list']) \
                .update(primary_node=id)
            VirtualMachine.objects \
                .filter(hostname__in=info['sinst_list']) \
                .update(secondary_node=id)
        
        print '    updated: %s out of %s' % (updated, len(infos))

        # batch update the cache updated time for all Nodes in this cluster. This
        # will set the last updated time for both Nodes that were modified and for
        # those that weren't.  even if it wasn't modified we want the last
        # updated time to be up to date.
        #
        # XXX don't bother checking to see whether this query needs to run.  With
        # normal usage it will almost always need to
        base.update(cached=datetime.now())

        self.timer.tick('records or timestamps updated')

    def _update_cache(self):
        """
        Updates the cache for all all VirtualMachines in all clusters.  This method
        processes the data in bulk, where possible, to reduce runtime.  Generally
        this should be faster than refreshing individual VirtualMachines.
        """
        self.timer = Timer()
        print '------[cache update]-------------------------------'
        for cluster in Cluster.objects.all():
            self._update_cluster(cluster)
        
        self.timer.stop()
        return self.timer.ticks

    @transaction.commit_on_success()
    def update_cache(self):
        return self._update_cache()



class CacheUpdateThread(Thread):
    def run(self):
        updater = NodeCacheUpdater()
        while True:
            updater.update_cache()
            time.sleep(settings.PERIODIC_CACHE_REFRESH)


if __name__ == '__main__':
    import getopt

    optlist, args = getopt.getopt(sys.argv[1:], 'd')
    if optlist and optlist[0][0] == '-d':
        #daemon
        CacheUpdateThread().start()

    else:
        NodeCacheUpdater().update_cache()
