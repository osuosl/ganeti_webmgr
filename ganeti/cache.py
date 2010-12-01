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


def update_cache():
    """
    Updates the cache for all all VirtualMachines in all clusters.  This method
    processes the data in bulk, where possible, to reduce runtime.  Generally
    this should be faster than refreshing individual VirtualMachines.
    """
    start = datetime.now()
    print '------[cache update]-------------------------------'
    for cluster in Cluster.objects.all():
        infos = cluster.instances(bulk=True)
        base = VirtualMachine.objects.all()
        no_updates = []
        
        for info in infos:
            vm, new = base.get_or_create(cluster=cluster, hostname=info['name'])
            if new or vm.mtime < datetime.fromtimestamp(info['mtime']) \
                or info['status'] != vm.info['status']:
                    print '    Virtual Machine (updated) : %s' % info['name']
                    # only update the whole object if it is new or modified. 
                    #
                    # XXX status changes will not always be reflected in mtime
                    # explicitly check status to see if it has changed.  failing
                    # to check this would result in state changes being lost
                    vm.info = info
                    vm.save()
            else:
                # no changes to this VirtualMachine
                print '    Virtual Machine : %s' % info['name']
                no_updates.append(vm.id)
            
        # batch update the cache update time for VMs that weren't modified
        if no_updates:
            base.filter(id__in=no_updates).update(cached=datetime.now())
    print '    Runtime: %s' % (datetime.now()-start)


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