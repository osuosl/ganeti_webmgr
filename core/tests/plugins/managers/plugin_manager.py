import unittest

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(PluginManager_Test)
        ])


class PluginManager_Test(unittest.TestCase):
    
    def test_register(self):
        pass
    
    def test_deregister(self):
        pass
    
    def test_registers(self):
        pass
    
    def test_contains(self):
        pass
    
    def test_getitem(self):
        pass