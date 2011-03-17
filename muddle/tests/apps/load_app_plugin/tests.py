from django.test import TestCase

from muddle.apps.module import load_app_plugin
from muddle.tests.apps.load_app_plugin.test_plugin import TestPlugin
from muddle.tests.apps.load_app_plugin import verify

TESTING_MODULE = 'tests.apps.load_app_plugin.file_for_testing_load_app_plugin'
WAS_RUN = False
CLASSES = []

class LoadAppPluginTestCase(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        global WAS_RUN, CLASSES
        WAS_RUN = False
        CLASSES = []

    def test_load_module(self):
        """
        Test Loading a plugin that just needs to load a module
        """
        load_app_plugin('tests.apps.load_app_plugin.file_for_test_load_module')
        self.assertTrue(verify.MODULE_LOADED)
    
    def test_load_module_with_method(self):
        """
        test loading a module using a method to process it
        """
        def method(module):
            global WAS_RUN
            WAS_RUN = True
            self.assertTrue(hasattr(module, 'AN_INTEGER'))
            self.assertEqual(1, module.AN_INTEGER)

        load_app_plugin(TESTING_MODULE, method=method)
        self.assertTrue(WAS_RUN)

    def test_load_module_with_error(self):
        """
        Test loading a module that has an error in it
        """
        def fail():
            load_app_plugin('tests.apps.load_app_plugin.file_for_testing_module_error')

        self.assertRaises(ZeroDivisionError, fail)

    def test_load_class_no_method(self):
        """
        test loading classes but without passing a method to use
        """
        def fail():
            load_app_plugin(TESTING_MODULE, TestPlugin)
        self.assertRaises(AssertionError, fail)
    
    def test_load_class(self):
        """
        Testing loading a plugin that looks for a specific class
        """
        def method(Klass):
            global WAS_RUN, CLASSES
            WAS_RUN = True
            self.assertTrue(issubclass(Klass, (TestPlugin)))
    
        load_app_plugin(TESTING_MODULE, TestPlugin, method)
        self.assertTrue(WAS_RUN)