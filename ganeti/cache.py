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
        print '    Total time: %s' %  (self.end - self.start)
    
    def tick(self, msg=''):
        now = datetime.now()
        print '    [%s] Time since last tick: %s' % (msg, (now-self.last_tick))
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
        print '%s:' % cluster.hostname
        infos = cluster.instances(bulk=True)
        timer.tick('ganeti fetch')
        
        base = cluster.virtual_machines.all()
        no_updates = []
        
        
        mtimes = base.values_list('hostname','mtime', 'id')
        d = {}
        for name, mtime, id in mtimes:
            d[name] = (mtime, id)
        timer.tick('mtimes fetched from db')
        
        
        for info in infos:
            
            try:
                #vm = base.get(hostname=info['name'])
                name = info['name']
                mtime, id = d[name]
                #print mtime
                
                if True: #\
                #or info['status'] != vm.info['status']:
                    #print '    Virtual Machine (updated) : %s' % name
                    #print '        %s :: %s' % (mtime, datetime.fromtimestamp(info['mtime']))
                    # only update the whole object if it is new or modified. 
                    #
                    # XXX status changes will not always be reflected in mtime
                    # explicitly check status to see if it has changed.  failing
                    # to check this would result in state changes being lost
                    vm = base.get(pk=id)
                    vm.info = info
                    vm.save()
                    timer.tick('save')
                else:
                    # no changes to this VirtualMachine
                    #print '    Virtual Machine : %s' % name
                    no_updates.append(id)
                
            except VirtualMachine.DoesNotExist:
                # new vm
                vm = VirtualMachine(cluster=cluster, hostname=info['name'])
                vm.info = info
                vm.save() 
        
        # batch update the cache update time for VMs that weren't modified
        if no_updates:
            base.filter(id__in=no_updates).update(cached=datetime.now())
        timer.tick('records or timestamps updated')
    timer.stop()

from django.db import transaction

@transaction.commit_on_success()
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
