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
    
    def start(self):
        self.start = datetime.now()
        self.last_tick = self.start
    
    def stop(self):
        self.end = datetime.now()
        print 'Time since last tick: %s' % (self.end-self.last_tick)
        print 'total time: %s' %  (self.end - self.start)
    
    def tick(self, msg=''):
        now = datetime.now()
        print '[%s] Time since last tick: %s' % (msg, (now-self.last_tick))
        self.last_tick = now


def _update_cache():
    """
    Updates the cache for all all VirtualMachines in all clusters.  This method
    processes the data in bulk, where possible, to reduce runtime.  Generally
    this should be faster than refreshing individual VirtualMachines.
    """
    timer = Timer()
    print '------[cache update]-------------------------------'
    for cluster in Cluster.objects.all():
        infos = cluster.instances(bulk=True)
        timer.tick('ganeti fetch')
        
        base = cluster.virtual_machines.all()
        no_updates = []
        
        
        mtimes = base.values_list('hostname','mtime')
        d = {}
        for x, y in mtimes:
            d[x] = y
        timer.tick('mtimes fetched')
        
        
        for info in infos:
            
            try:
                #vm = base.get(hostname=info['name'])
                mtime = d[info['name']]
                print mtime
                
                if not mtime or mtime < datetime.fromtimestamp(info['mtime']): #\
                #or info['status'] != vm.info['status']:
                    print '    Virtual Machine (updated) : %s' % info['name']
                    # only update the whole object if it is new or modified. 
                    #
                    # XXX status changes will not always be reflected in mtime
                    # explicitly check status to see if it has changed.  failing
                    # to check this would result in state changes being lost
                    vm = base.get(hostname=info['name'])
                    vm.info = info
                    vm.save()
                else:
                    # no changes to this VirtualMachine
                    print '    Virtual Machine : %s' % info['name']
                    no_updates.append(vm.id)
                
            except VirtualMachine.DoesNotExist:
                # new vm
                vm = VirtualMachine(cluster=cluster, hostname=info['name'])
                vm.info = info
                vm.save()
        
        timer.tick('records processed')
        
        # batch update the cache update time for VMs that weren't modified
        if no_updates:
            base.filter(id__in=no_updates).update(cached=datetime.now())
    timer.stop()

from django.db import transaction

def update_cache():
    #with transaction.commit_on_success():
    _update_cache()



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