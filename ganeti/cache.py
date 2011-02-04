# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
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


from django.conf import settings
from ganeti.models import Cluster, VirtualMachine


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


def _update_cache():
    """
    Updates the cache for all all VirtualMachines in all clusters.  This method
    processes the data in bulk, where possible, to reduce runtime.  Generally
    this should be faster than refreshing individual VirtualMachines.
    """
    timer = Timer()
    print '------[cache update]-------------------------------'
    for cluster in Cluster.objects.all():
        print '%s:' % cluster.hostname
        base = cluster.virtual_machines.all()
        infos = cluster.instances(bulk=True)
        timer.tick('info fetched from ganeti     ')
        updated = 0
        
        mtimes = base.values_list('hostname', 'id', 'mtime', 'status')
        d = {}
        for name, id, mtime, status in mtimes:
            d[name] = (id, float(mtime) if mtime else None, status)
        timer.tick('mtimes fetched from db       ')
        
        for info in infos:
            name = info['name']
            if name in d:
                id, mtime, status = d[name]
                if not mtime or mtime < info['mtime'] \
                or status != info['status']:
                    #print '    Virtual Machine (updated) : %s' % name
                    #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
                    # only update the whole object if it is new or modified. 
                    #
                    # XXX status changes will not always be reflected in mtime
                    # explicitly check status to see if it has changed.  failing
                    # to check this would result in state changes being lost
                    data = VirtualMachine.parse_persistent_info(info)
                    VirtualMachine.objects.filter(pk=id) \
                        .update(serialized_info=cPickle.dumps(info), **data)
                    updated += 1
            else:
                # new vm
                vm = VirtualMachine(cluster=cluster, hostname=info['name'])
                vm.info = info
                vm.save() 
        
        # batch update the cache updated time for all VMs in this cluster. This
        # will set the last updated time for both VMs that were modified and for
        # those that weren't.  even if it wasn't modified we want the last
        # updated time to be up to date.
        #
        # XXX don't bother checking to see whether this query needs to run.  It
        # normal usage it will almost always need to
        base.update(cached=datetime.now())
        
        timer.tick('records or timestamps updated')
    print '    updated: %s out of %s' % (updated, len(infos))
    timer.stop()
    return timer.ticks


from django.db import transaction

@transaction.commit_on_success()
def update_cache():
    #with transaction.commit_on_success():
    return _update_cache()



class CacheUpdateThread(Thread):
    def run(self):
        while True:
            update_cache()
            time.sleep(settings.PERIODIC_CACHE_REFRESH)


if __name__ == '__main__':
    import getopt
    
    optlist, args = getopt.getopt(sys.argv[1:], 'd')
    if optlist and optlist[0][0] == '-d':
        #daemon
        CacheUpdateThread().start()
        
    else:
        update_cache()
