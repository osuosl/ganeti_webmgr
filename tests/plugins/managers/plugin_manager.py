import unittest

from muddle.plugins.plugin_manager import PluginManager
from muddle.plugins.registerable import Registerable

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(PluginManager_Test)
        ])


class TestRegisterable(Registerable):
    pass

class PluginManager_Test(unittest.TestCase):
    
    def test_register(self):
        """
        Tests registering a Registerable
        """
        manager = PluginManager()
        r = Registerable()
        manager.register(r)
        self.assert_(len(manager.enabled)==1, manager.enabled)
        self.assert_(len(manager.plugins)==1, manager.plugins)
        self.assert_(r.name() in manager, manager.enabled)
        self.assert_(r.name() in manager, manager.plugins)
    
    def test_deregister_by_name(self):
        """
        Tests deregistering a Registerable using its Registerable, name()
        """
        manager = PluginManager()
        r = Registerable()
        manager.register(r)
        manager.deregister(r.name())
        self.assert_(len(manager.enabled)==0, manager.enabled)
        self.assert_(len(manager.plugins)==0, manager.plugins)
        self.assertFalse(r.name() in manager.enabled, manager.enabled)
        self.assertFalse(r.name() in manager.plugins, manager.plugins)
    
    def test_deregister_by_registerable(self):
        """
        Tests deregistering a Registerable using a Registerable instance
        """
        manager = PluginManager()
        r = Registerable()
        manager.register(r)
        manager.deregister(r)
        self.assert_(len(manager.enabled)==0, manager.enabled)
        self.assert_(len(manager.plugins)==0, manager.plugins)
        self.assertFalse(r.name() in manager.enabled, manager.enabled)
        self.assertFalse(r.name() in manager.plugins, manager.plugins)
    
    def test_registers(self):
        """
        Tests registering several registerables
        """
        manager = PluginManager()
        a = Registerable()
        b = TestRegisterable()
        manager.registers((a,b))
        self.assert_(len(manager.enabled)==2, manager.enabled)
        self.assert_(len(manager.plugins)==2, manager.plugins)
        self.assert_(a.name() in manager, manager.enabled)
        self.assert_(a.name() in manager, manager.plugins)
        self.assert_(b.name() in manager, manager.enabled)
        self.assert_(b.name() in manager, manager.plugins)
    
    def test_contains(self):
        """
        Tests using "name in manager" syntax
        """
        manager = PluginManager()
        r = Registerable()
        manager.register(r)
        self.assert_(r.name() in manager, manager.enabled)
    
    def test_getitem(self):
        """
        Tests retrieving an item using "manager[name]" syntax
        """
        manager = PluginManager()
        r = Registerable()
        manager.register(r)
        self.assert_(r==manager[r.name()], manager.enabled)
    
    def test_len(self):
        """
        Tests len operator:  len(manager)
        """
        manager = PluginManager()
        r = Registerable()
        self.assert_(len(manager)==0, manager.enabled)
        manager.register(r)
        self.assert_(len(manager)==1, manager.enabled)