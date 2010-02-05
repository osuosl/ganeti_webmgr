import unittest

from plugin_manager import suite as plugin_manager_suite
from root_plugin_manager import suite as root_plugin_manager_suite

def suite():
    return unittest.TestSuite([
            plugin_manager_suite(),
            root_plugin_manager_suite()
        ])