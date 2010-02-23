import unittest

from muddle.tests.test_plugins import *
from muddle.plugins.plugin import *
from muddle.plugins.plugin_manager import *

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(Plugin_Test)
        ])

class Plugin_Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_depends_no_depends(self):
        """
        Tests getting depends when plugin depends on nothing
        """
        depends = PluginNoDepends.get_depends()
        self.assert_(len(depends)==0,'Depends should be 0')

    def test_get_depends_depends_one(self):
        """
        Tests getting depends when plugin depends on only one plugin
        """
        depends = PluginOneDepends.get_depends()
        self.assert_(len(depends)==1,'Depends should be 1')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
    
    def test_get_depends_depends_two(self):
        """
        Tests getting depends when plugin depends on more than one plugin
        """
        depends = PluginTwoDepends.get_depends()
        self.assert_(len(depends)==2,'Depends should be 2')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
        self.assert_(PluginNoDependsB in depends, 'Depends does not contain PluginNoDependsB')
    
    def test_get_depends_recursive(self):
        """
        Tests getting depends when plugin depends on a plugin with its own
        depends
        """
        depends = PluginRecursiveDepends.get_depends()
        self.assert_(len(depends)==2,'Depends should be 2')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
        self.assert_(PluginOneDepends in depends, 'Depends does not contain PluginRecursiveDepends')
        self.assert_(depends[0]==PluginNoDepends, 'Depends out of order')
        self.assert_(depends[1]==PluginOneDepends, 'Depends out of order')
    
    def test_get_depends_recursive_redundant(self):
        """
        Tests getting depends when plugin depends on a plugin with its own
        depends but that dependencies was already added
        """
        depends = PluginRedundantRecursiveDepends.get_depends()
        self.assert_(len(depends)==2,'Depends should be 2')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
        self.assert_(PluginOneDepends in depends, 'Depends does not contain PluginRecursiveDepends')
        self.assert_(depends[0]==PluginNoDepends, 'Depends out of order')
        self.assert_(depends[1]==PluginOneDepends, 'Depends out of order')
    
    def test_get_depends_redundant(self):
        """
        Tests getting depends when plugin depends on the same plugin twice
        """
        depends = PluginRedundentDepends.get_depends()
        self.assert_(len(depends)==1,'Depends should be 1')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
    
    def test_get_depends_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle
        """
        self.assertRaises(CyclicDependencyException, PluginCycleA.get_depends)
        self.assertRaises(CyclicDependencyException, PluginCycleB.get_depends)
    
    def test_get_depends_indirect_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle through
        another depend
        """
        return
        self.assertRaises(CyclicDependencyException, PluginIndirectCycleA.get_depends)
        self.assertRaises(CyclicDependencyException, PluginIndirectCycleB.get_depends)
        self.assertRaises(CyclicDependencyException, PluginIndirectCycleC.get_depends)
    
    def test_get_depended_no_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with nothing depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        plugin = manager.enable('PluginNoDepends')
        dependeds = plugin.get_depended()
        self.assert_(len(dependeds)==0, 'Plugin has nothing depending on it')

    def test_get_depended_one_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with only one other module depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        plugin = manager.enable('PluginNoDepends')
        depended = manager.enable('PluginOneDepends')
        dependeds = plugin.get_depended()
        self.assert_(len(dependeds)==1, len(dependeds))
        self.assert_(depended in dependeds, dependeds)

    def test_get_depended_two_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with two other modules depending on it
        
        given B->A and C->A
        Dependeds(A) = (A, C)
        Dependeds(B) = ()
        Dependeds(C) = ()
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.register(PluginOneDependsB)
        pluginA = manager.enable('PluginNoDepends')
        pluginB = manager.enable('PluginOneDepends')
        pluginC = manager.enable('PluginOneDependsB')
        dependedsA = pluginA.get_depended()
        self.assert_(len(dependedsA)==2, len(dependedsA))
        self.assert_(pluginB in dependedsA)
        self.assert_(pluginC in dependedsA)
        dependedsB = pluginB.get_depended()
        self.assert_(len(dependedsB)==0, len(dependedsB))
        dependedsC = pluginC.get_depended()
        self.assert_(len(dependedsC)==0, len(dependedsC))

    def test_get_depended_two_depends(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with a depended that also depends on another plugin.
        
        ie. given C->A and C->B.
            Dependeds(A) = (C)
            Dependeds(B) = (C)
            Dependeds(C) = ()
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginNoDependsB)
        manager.register(PluginTwoDepends)
        pluginA = manager.enable('PluginNoDepends')
        pluginB = manager.enable('PluginNoDependsB')
        pluginC = manager.enable('PluginTwoDepends')
        dependedsA = pluginA.get_depended()
        self.assert_(len(dependedsA)==1, len(dependedsA))
        self.assert_(pluginC in dependedsA)
        dependedsB = pluginB.get_depended()
        self.assert_(len(dependedsB)==1, len(dependedsB))
        self.assert_(pluginC in dependedsB)
        dependedsC = pluginC.get_depended()
        self.assert_(len(dependedsC)==0, len(dependedsC))

    def test_get_depended_recursive_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with two modules depending on it, one with a recursive depend
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.register(PluginRecursiveDepends)
        plugin = manager.enable('PluginNoDepends')
        dependedA = manager.enable('PluginOneDepends')
        dependedB = manager.enable('PluginRecursiveDepends')
        dependeds = plugin.get_depended()
        self.assert_(len(dependeds)==2, len(dependeds))
        self.assert_(dependedA in dependeds)
        self.assert_(dependedB in dependeds)