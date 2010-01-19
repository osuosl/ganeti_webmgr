import unittest

from maintain.core.plugins import *
from test_plugins import *

class RootPluginManager_Test(unittest.TestCase):
    def test_register(self):
        """
        Tests registering plugins with no dependencies
        """
        manager = RootPluginManager()
        self.assert_(len(manager.plugins)==0, 'plugins should be empty')
        manager.register(PluginNoDepends)
        self.assert_(len(manager.plugins)==1, 'plugins should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.plugins.keys(), 'plugins should contain PluginNoDepends')

    def test_enable(self):
        """
        Tests enable plugins with no dependencies
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')

    def test_enable_redundant(self):
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')

    def test_enable_before_register(self):
        """
        Tests enable plugins with no dependencies
        """
        manager = RootPluginManager()
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertRaises(UnknownPluginException, manager.enable, 'PluginNoDepends')
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertFalse('PluginNoDepends' in manager.enabled, 'enabled should not contain PluginNoDepends')
    
    def test_enable_depends(self):
        """
        Tests enable plugins with a dependency
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assert_(manager.enable('PluginOneDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==2, 'enabled should have 2 plugins')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assert_('PluginOneDepends' in manager.enabled, 'enabled should contain PluginOneDepends')
    
    def test_enable_exception(self):
        """
        Tests enable plugin that throws exception
        """
        manager = RootPluginManager()
        manager.register(PluginFailsWhenEnabled)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailsWhenEnabled')
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertFalse('PluginFailsWhenEnabled' in manager.enabled, 'enabled should not contain PluginFailsWhenEnabled')

    def test_enable_depends_exception(self):
        """
        Tests enable plugins where first dependency throws exception
        """
        manager = RootPluginManager()
        manager.register(PluginFailingDepends)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailingDepends')
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertFalse('PluginFailsWhenEnabled' in manager.enabled, 'enabled should not contain PluginFailsWhenEnabled')
        self.assertFalse('PluginFailingDepends' in manager.enabled, 'enabled should not contain PluginFailingDepends')
    
    def test_enable_depends_exception_with_rollback(self):
        """
        Tests enable plugins with multiple dependencies, and an exception is
        thrown after one or more dependencies have already been enabled
        """
        manager = RootPluginManager()
        manager.register(PluginFailsWithDepends)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailsWithDepends')
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assertFalse('PluginFailsWithDepends' in manager.enabled, 'enabled should not contain PluginFailsWithDepends')
        self.assertFalse('PluginNoDepends' in manager.enabled, 'enabled should not contain PluginNoDepends')

    def test_enable_depends_exception_with_rollback_depends_already_enabled(self):
        """
        Tests enable plugins with multiple dependencies, and an exception is
        thrown after one or more dependencies have already been enabled.  This
        version one dependency was already enabled and should not be rolled back
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginNoDependsB)
        manager.register(PluginFailsWhenEnabled)
        manager.register(PluginDependsFailsRequiresRollback)
        self.assert_(len(manager.enabled)==0, 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assertRaises(Exception, manager.enable, 'PluginDependsFailsRequiresRollback')
        self.assert_(len(manager.enabled)==1, 'enabled should have only 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assertFalse('PluginDependsFailsRequiresRollback' in manager.enabled, 'enabled should not contain PluginDependsFailsRequiresRollback')
        self.assertFalse('PluginFailsWhenEnabled' in manager.enabled, 'enabled should not contain PluginFailsWhenEnabled')
        self.assertFalse('PluginNoDependsB' in manager.enabled, 'enabled should not contain PluginNoDependsB')
    
    def test_disable(self):
        """
        tests disabling a plugin with nothing depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.enable('PluginNoDepends')
        manager.disable('PluginNoDepends')
        self.assert_(len(manager.enabled)==0, len(manager.enabled))

    def test_disable_with_dependeds(self):
        """
        tests disabling a plugin with other plugins depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.enable('PluginOneDepends')
        self.assert_(len(manager.enabled)==2, len(manager.enabled))
        manager.disable('PluginNoDepends')
        self.assert_(len(manager.enabled)==0, len(manager.enabled))
        
    def test_disable_with_dependeds_and_depend(self):
        """
        Tests disabling a plugin that has both dependeds and depends.  The
        depended plugins will generate a list of depends including the plugin
        that the disablee depends on.  this tests that that plugin is NOT
        disabled
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.register(PluginRecursiveDepends)
        manager.enable('PluginRecursiveDepends')
        self.assert_(len(manager.enabled)==3, len(manager.enabled))
        manager.disable('PluginOneDepends')
        self.assert_(len(manager.enabled)==1, len(manager.enabled))
        self.assert_('PluginNoDepends' in manager.enabled, manager.enabled)


class Plugin_Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_depends_no_depends(self):
        """
        Tests getting depends when plugin depends on nothing
        """
        depends = get_depends(PluginNoDepends)
        self.assert_(len(depends)==0,'Depends should be 0')

    def test_get_depends_depends_one(self):
        """
        Tests getting depends when plugin depends on only one plugin
        """
        depends = get_depends(PluginOneDepends)
        self.assert_(len(depends)==1,'Depends should be 1')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
    
    def test_get_depends_depends_two(self):
        """
        Tests getting depends when plugin depends on more than one plugin
        """
        depends = get_depends(PluginTwoDepends)
        self.assert_(len(depends)==2,'Depends should be 2')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
        self.assert_(PluginNoDependsB in depends, 'Depends does not contain PluginNoDependsB')
    
    def test_get_depends_recursive(self):
        """
        Tests getting depends when plugin depends on a plugin with its own
        depends
        """
        depends = get_depends(PluginRecursiveDepends)
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
        depends = get_depends(PluginRedundantRecursiveDepends)
        self.assert_(len(depends)==2,'Depends should be 2')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
        self.assert_(PluginOneDepends in depends, 'Depends does not contain PluginRecursiveDepends')
        self.assert_(depends[0]==PluginNoDepends, 'Depends out of order')
        self.assert_(depends[1]==PluginOneDepends, 'Depends out of order')
    
    def test_get_depends_redundant(self):
        """
        Tests getting depends when plugin depends on the same plugin twice
        """
        depends = get_depends(PluginRedundentDepends)
        self.assert_(len(depends)==1,'Depends should be 1')
        self.assert_(PluginNoDepends in depends, 'Depends does not contain PluginNoDepends')
    
    def test_get_depends_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle
        """
        self.assertRaises(CyclicDependencyException, get_depends, PluginCycleA)
        self.assertRaises(CyclicDependencyException, get_depends, PluginCycleB)
    
    def test_get_depends_indirect_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle through
        another depend
        """
        return
        self.assertRaises(CyclicDependencyException, get_depends, PluginIndirectCycleA)
        self.assertRaises(CyclicDependencyException, get_depends, PluginIndirectCycleB)
        self.assertRaises(CyclicDependencyException, get_depends, PluginIndirectCycleC)
    
    def test_get_depended_no_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with nothing depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        plugin = manager.enable('PluginNoDepends')
        dependeds = get_depended(plugin)
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
        dependeds = get_depended(plugin)
        self.assert_(len(dependeds)==1, len(dependeds))
        self.assert_(depended in dependeds, dependeds)

    def test_get_depended_two_dependeds(self):
        """
        Tests getting the list of modules a module depends on.  for a module
        with two other modules depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.register(PluginOneDependsB)
        plugin = manager.enable('PluginNoDepends')
        dependedA = manager.enable('PluginOneDepends')
        dependedB = manager.enable('PluginOneDependsB')
        dependeds = get_depended(plugin)
        self.assert_(len(dependeds)==2, len(dependeds))
        self.assert_(dependedA in dependeds)
        self.assert_(dependedB in dependeds)
    
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
        dependeds = get_depended(plugin)
        self.assert_(len(dependeds)==2, len(dependeds))
        self.assert_(dependedA in dependeds)
        self.assert_(dependedB in dependeds)


def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(RootPluginManager_Test),
            unittest.TestLoader().loadTestsFromTestCase(Plugin_Test)
        ])

