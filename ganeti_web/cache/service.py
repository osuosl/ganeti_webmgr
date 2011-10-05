from twisted.application.service import Service
from twisted.internet.defer import DeferredList
from twisted.internet.task import LoopingCall

from django.conf import settings

from ganeti_web.cache.node import NodeCacheUpdater
from ganeti_web.cache.virtual_machine import VirtualMachineCacheUpdater
from ganeti_web.cache.cluster import ClusterCacheUpdater
from ganeti_web.cache.job import JobCacheUpdater


class CacheService(Service):

    def __init__(self, *args, **kwargs):
        self.call = None

        self.node_updater = NodeCacheUpdater()
        self.cluster_updater = ClusterCacheUpdater()
        self.vm_updater = VirtualMachineCacheUpdater()
        self.job_updater = JobCacheUpdater()

    def update_cache(self):
        """ a single run of all update classes """
        return DeferredList([
                            self.vm_updater.update(),
                            self.job_updater.update(),
                            self.node_updater.update(),
                            self.cluster_updater.update(),
                            ])
    
    def startService(self):
        self.call = LoopingCall(self.update_cache)
        self.call.start(settings.PERIODIC_CACHE_REFRESH)
    
    def stopService(self):
        if self.call is not None:
            self.call.stop()
