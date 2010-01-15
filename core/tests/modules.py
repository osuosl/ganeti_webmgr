import unittest

from maintain.core.modules import Plugin, PluginManager, get_depends, \
CyclicDependencyException


class PluginA(Plugin):
    pass

class PluginB(Plugin):
    depends = (PluginA)
    
class PluginC(Plugin):
    depends = (PluginB)
    
class PluginD(Plugin):
    depends = (PluginB, PluginA)
    
class PluginE(Plugin):
    pass

class PluginF(Plugin):
    depends = (PluginA, PluginE)

class PluginG(Plugin):
    depends = (PluginA, PluginA)
    
class PluginH(Plugin):
    depends = (PluginB, PluginC, PluginA)

class PluginI(Plugin):
    pass
    
class PluginJ(Plugin):
    depends = (PluginI)
PluginI.depends = (PluginJ)


class PluginK(Plugin):
    pass
    
class PluginL(Plugin):
    depends = (PluginK)

class PluginM(Plugin):
    depends = (PluginL)
PluginK.depends = (PluginM)

class PluginManager_Test(unittest.TestCase):
    def test_register(self):
        """
        Tests registering plugins with no dependencies
        """
        pass

    def test_register(self):
        """
        Tests registering plugins with no dependencies
        """
        pass
    
    

class Plugin_Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_depends_no_depends(self):
        """
        Tests getting depends when plugin depends on nothing
        """
        depends = get_depends(PluginA)
        self.assertTrue(len(depends)==0,'Depends should be 0')

    def test_get_depends_depends_one(self):
        """
        Tests getting depends when plugin depends on only one plugin
        """
        depends = get_depends(PluginB)
        self.assertTrue(len(depends)==1,'Depends should be 1')
        self.assertTrue(PluginA in depends, 'Depends does not contain PluginA')
    
    def test_get_depends_depends_two(self):
        """
        Tests getting depends when plugin depends on more than one plugin
        """
        depends = get_depends(PluginF)
        self.assertTrue(len(depends)==2,'Depends should be 2')
        self.assertTrue(PluginA in depends, 'Depends does not contain PluginA')
        self.assertTrue(PluginE in depends, 'Depends does not contain PluginE')
    
    def test_get_depends_recursive(self):
        """
        Tests getting depends when plugin depends on a plugin with its own
        depends
        """
        depends = get_depends(PluginC)
        self.assertTrue(len(depends)==2,'Depends should be 2')
        self.assertTrue(PluginA in depends, 'Depends does not contain PluginA')
        self.assertTrue(PluginB in depends, 'Depends does not contain PluginB')
    
    def test_get_depends_recursive_redundant(self):
        """
        Tests getting depends when plugin depends on a plugin with its own
        depends but that dependencies was already added
        """
        depends = get_depends(PluginD)
        self.assertTrue(len(depends)==2,'Depends should be 2')
        self.assertTrue(PluginA in depends, 'Depends does not contain PluginA')
        self.assertTrue(PluginB in depends, 'Depends does not contain PluginB')
        self.assertTrue(depends[0]==PluginA, 'Depends out of order')
        self.assertTrue(depends[1]==PluginB, 'Depends out of order')
    
    def test_get_depends_redundant(self):
        """
        Tests getting depends when plugin depends on the same plugin twice
        """
        depends = get_depends(PluginG)
        self.assertTrue(len(depends)==1,'Depends should be 1')
        self.assertTrue(PluginA in depends, 'Depends does not contain PluginA')
    
    def test_get_depends_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle
        """
        self.assertRaises(CyclicDependencyException, get_depends, PluginJ)
        
    
    def test_get_depends_indirect_cycle(self):
        """
        Tests getting depends from a plugin that has a dependency cycle through
        another depend
        """
        return
        self.assertRaises(CyclicDependencyException, get_depends, PluginK)
    
def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(PluginManager_Test),
            unittest.TestLoader().loadTestsFromTestCase(Plugin_Test)
        ])

