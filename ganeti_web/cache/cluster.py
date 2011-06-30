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

# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from twisted.internet import reactor
from twisted.internet.defer import DeferredList, Deferred
from twisted.web import client
from ganeti_web.cache import Timer, Counter
from ganeti_web.models import Cluster, VirtualMachine


CLUSTERS_URL = 'https://%(hostname)s:%(port)s/2/info'


class ClusterCacheUpdater(object):

    def update(self):
        """
        Updates the cache for all all Clusters.  This method must query clusters
        individually.  This is faster than lazy cache only because it only
        happens once, whereas it may happen multiple times using the lazy
        mechanism
        """
        self.timer = Timer()
        print '------[cluster cache update]-------------------------------'
        clusters = Cluster.objects.all().values('id','hostname','mtime','port')
        deferreds = [self.get_cluster_info(data) for data in clusters]
        deferred_list = DeferredList(deferreds)
        deferred_list.addCallback(self.complete)
        
        return deferred_list

    def get_cluster_info(self, data):
        """
        fetch cluster info from ganeti
        """
        deferred = Deferred()
        url = str(CLUSTERS_URL % data)
        d = client.getPage(url)
        d.addCallback(self.process_cluster_info, data, deferred.callback)

        # XXX even when the get fails we want to send the callback so the loop
        # does not stop because a single cluster had an error
        def error(*args, **kwargs):
            print 'ERROR retrieving: %s ' % url
            deferred.callback(None)
        d.addErrback(error)
        
        return deferred
    
    def process_cluster_info(self, info, data, callback):
        """
        process data received from ganeti.

        @param info - info from ganeti
        @param data - data from database
        @param callback - callback fired when method is complete.
        """
        print '%s:' % data['hostname']
        info = json.loads(info)
        self.timer.tick('info fetched from ganeti     ')

        deferred = Deferred()
        args = (info, data, deferred.callback)
        reactor.callLater(0, self.update_cluster, *args)

        # XXX it would be nice if the deferred could be returned and this
        # callback hooked up outside of the method, but that doesn't seem
        # possible
        deferred.addCallback(callback)

    def update_cluster(self, info, data, callback):
        """
        updates an individual Cluster, this is the actual work function

        @param info - info from ganeti
        @param data - data from database
        @param callback - callback fired when method is complete.
        """
        mtime = data['mtime']
        if not mtime or mtime < info['mtime']:
            print '    Cluster (updated) : %(hostname)s' % data
            #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
            # only update the whole object if it is new or modified.
            #
            parsed = Cluster.parse_persistent_info(info)
            Cluster.objects.filter(pk=data['id']) \
                .update(serialized_info=cPickle.dumps(info), **parsed)
        callback(data['id'])

    def complete(self, result):
        """ callback fired when everything is complete """

        # batch update the cache updated time for all VMs in this cluster. This
        # will set the last updated time for both VMs that were modified and for
        # those that weren't.  even if it wasn't modified we want the last
        # updated time to be up to date.
        #
        # XXX don't bother checking to see whether this query needs to run.  It
        # normal usage it will almost always need to
        Cluster.objects.update(cached=datetime.now())
        self.timer.tick('records or timestamps updated')
        self.timer.stop()
