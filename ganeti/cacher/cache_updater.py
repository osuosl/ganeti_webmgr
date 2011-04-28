from twisted.internet.defer import DeferredList
from ganeti.cacher.node import NodeCacheUpdater

class CacheUpdater(object):

    def __init__(self):
        self.node_updater = NodeCacheUpdater()
        #self.vm_updater = VirtualMachineCacheUpdater()

    def update_cache(self):
        """ a single run of the updaters """
        return DeferredList([self.node_updater.update_cache(),
                            self.vm_updater.update_cache()])
    
    def periodic_updates(self):
        deferred = self.update_cache()