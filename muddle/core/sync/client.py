from multiprocessing.managers import SyncManager


class MultiProcessPluginManager(SyncManager):
    """
    Syncronization manager that enables synchronization between multiple muddle
    RootPluginManagers
    """
    def __init__(self, *args, **kwargs):
        super(MultiProcessPluginManager, self).__init__(*args, **kwargs)

    def get_enabled(self):
        return self.enabled





if __name__ == '__main__':

    
    MultiProcessPluginManager.register('get_enabled')
    MultiProcessPluginManager.register('wtf')
    
    manager = MultiProcessPluginManager(address=('', 61000), authkey='goaway123984')
    manager.connect()
    
    
    
    wtf = manager.wtf()
    print '>>> wtf %s' % wtf.get()
    d = wtf.get()
    d[1] = 3
    print d
    print '>>> wtf %s' % wtf.get()
