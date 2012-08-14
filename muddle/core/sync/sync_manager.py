from multiprocessing import RLock
from multiprocessing.managers import SyncManager


class MultiProcessPluginManager(SyncManager):
    """
    Syncronization manager that enables synchronization between multiple muddle
    RootPluginManagers
    """

duh = None
class WTFProxy ():
    enabled = None
    
    def get(self):
        global duh
        return duh
    
    def set(self, v):
        global duh
        duh = v

if __name__ == '__main__':
    enabled = {}
    lock = RLock()
    
    MultiProcessPluginManager.register('get_enabled', lambda:enabled)
    MultiProcessPluginManager.register('wtf', WTFProxy)
    manager = MultiProcessPluginManager(address=('', 61000), authkey='goaway123984')
    manager.start()
    
    d = manager.dict()
    duh = d
    manager.wtf().set(d)
    print duh, d
    manager.join()
