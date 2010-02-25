import unittest

from test_plugins import *
from muddle.plugins import CyclicDependencyException, UnknownPluginException
from muddle.plugins.managers.plugin_manager import PluginManager
from muddle.plugins.managers.root_plugin_manager import RootPluginManager

from django.conf import settings
core = len(settings.CORE_PLUGINS)

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(RootPluginManager_Test)
        ])

class RootPluginManager_Test(unittest.TestCase):
    def test_register(self):
        """
        Tests registering plugins with no dependencies
        """
        manager = RootPluginManager()
        self.assert_(len(manager.plugins)==core, 'plugins should be empty')
        manager.register(PluginNoDepends)
        self.assert_(len(manager.plugins)==core+1, 'plugins should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.plugins.keys(), 'plugins should contain PluginNoDepends')

    def test_enable(self):
        """
        Tests enable plugins with no dependencies
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==core+1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')

    def test_enable_redundant(self):
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        self.assert_(len(manager.enabled)==core , 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==core+1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==core+1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')

    def test_enable_before_register(self):
        """
        Tests enable plugins with no dependencies
        """
        manager = RootPluginManager()
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertRaises(UnknownPluginException, manager.enable, 'PluginNoDepends')
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertFalse('PluginNoDepends' in manager.enabled, 'enabled should not contain PluginNoDepends')
    
    def test_enable_depends(self):
        """
        Tests enable plugins with a dependency
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assert_(manager.enable('PluginOneDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==core+2, 'enabled should have 2 plugins')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assert_('PluginOneDepends' in manager.enabled, 'enabled should contain PluginOneDepends')
    
    def test_enable_exception(self):
        """
        Tests enable plugin that throws exception
        """
        manager = RootPluginManager()
        manager.register(PluginFailsWhenEnabled)
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailsWhenEnabled')
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertFalse('PluginFailsWhenEnabled' in manager.enabled, 'enabled should not contain PluginFailsWhenEnabled')

    def test_enable_depends_exception(self):
        """
        Tests enable plugins where first dependency throws exception
        """
        manager = RootPluginManager()
        manager.register(PluginFailingDepends)
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailingDepends')
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertFalse('PluginFailsWhenEnabled' in manager.enabled, 'enabled should not contain PluginFailsWhenEnabled')
        self.assertFalse('PluginFailingDepends' in manager.enabled, 'enabled should not contain PluginFailingDepends')
    
    def test_enable_depends_exception_with_rollback(self):
        """
        Tests enable plugins with multiple dependencies, and an exception is
        thrown after one or more dependencies have already been enabled
        """
        manager = RootPluginManager()
        manager.register(PluginFailsWithDepends)
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assertRaises(Exception, manager.enable, 'PluginFailsWithDepends')
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
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
        self.assert_(len(manager.enabled)==core, 'enabled should be empty')
        self.assert_(manager.enable('PluginNoDepends'), 'enable returned False')
        self.assert_(len(manager.enabled)==core+1, 'enabled should only have 1 plugin')
        self.assert_('PluginNoDepends' in manager.enabled, 'enabled should contain PluginNoDepends')
        self.assertRaises(Exception, manager.enable, 'PluginDependsFailsRequiresRollback')
        self.assert_(len(manager.enabled)==core+1, 'enabled should have only 1 plugin')
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
        self.assert_(len(manager.enabled)==core, len(manager.enabled))

    def test_disable_with_dependeds(self):
        """
        tests disabling a plugin with other plugins depending on it
        """
        manager = RootPluginManager()
        manager.register(PluginNoDepends)
        manager.register(PluginOneDepends)
        manager.enable('PluginOneDepends')
        self.assert_(len(manager.enabled)==core+2, len(manager.enabled))
        manager.disable('PluginNoDepends')
        self.assert_(len(manager.enabled)==core, len(manager.enabled))
        
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
        self.assert_(len(manager.enabled)==core+3, len(manager.enabled))
        manager.disable('PluginOneDepends')
        self.assert_(len(manager.enabled)==core+1, len(manager.enabled))
        self.assert_('PluginNoDepends' in manager.enabled, manager.enabled)