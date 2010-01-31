import unittest

from core.models import *
from core.plugins.registerable import PERM_READ, PERM_WRITE, PERM_CREATE, \
    PERM_DELETE, PERM_ALL, PERM_NONE
from core.plugins.plugin_manager import *
from core.plugins.model_support import *
from tests.models import *

import settings

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(ModelView_Test)
        ])

class ModelView_Test(unittest.TestCase):
    def setUp(self):
        if not 'tests' in settings.INSTALLED_APPS:
            raise Exception('Test models are not installed tests cannot run')
        
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)
        
    def tearDown(self):
        pass
    
    def test_register_simple(self):
        simple= ModelWrapper(Simple)
        self.manager.register(simple)
        self.assert_('Simple' in self.manager, self.manager.enabled)
        self.assert_('value' in simple.fields, simple.fields)
        self.assert_(len(simple.fields)==1, simple.fields)
    
    def test_register_complex_no_related_registered(self):
        """
        Tests registering an object with relations when none of the
        relations are registered
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.assert_('Complex' in self.manager, self.manager.enabled)
        self.assert_(len(complex.fields)==0, complex.fields)
        self.assert_(len(complex.one_to_many)==0, complex.one_to_many)
        self.assert_(len(complex.one_to_one)==0, complex.one_to_one)
    
    def test_register_1_1_parent_first(self):
        """
        Test registering a 1:1 related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        one_to_one = ModelWrapper(OneToOne)
        self.manager.register(one_to_one)
        self.assert_(len(complex.one_to_one)==1, complex.one_to_one)
        self.assert_(len(one_to_one.one_to_one)==1, one_to_one.one_to_one)
        self.assert_('OneToOne' in complex.one_to_one, complex.one_to_one)
        self.assert_('Complex' in one_to_one.one_to_one, one_to_one.one_to_one)
        
    def test_register_1_1_parent_second(self):
        """
        Test registering a 1:1 related object
        """
        one_to_one = ModelWrapper(OneToOne)
        self.manager.register(one_to_one)
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.assert_(len(complex.one_to_one)==1, complex.__dict__)
        self.assert_(len(one_to_one.one_to_one)==1, one_to_one.one_to_one)
        self.assert_('OneToOne' in complex.one_to_one, complex.one_to_one)
        self.assert_('Complex' in one_to_one.one_to_one, one_to_one.one_to_one)
    
    def test_register_1_M_parent_first(self):
        """
        Test registering a 1:M related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        one_to_many = ModelWrapper(OneToMany)
        self.manager.register(one_to_many)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_(len(one_to_many.many_to_one)==1, one_to_many.many_to_one)
        self.assert_('OneToMany' in complex.one_to_many, complex.one_to_many)
        self.assert_('Complex' in one_to_many.many_to_one, one_to_many.many_to_one)
        
    def test_register_1_M_parent_second(self):
        """
        Test registering a 1:M related object
        """
        one_to_many = ModelWrapper(OneToMany)
        self.manager.register(one_to_many)
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_(len(one_to_many.many_to_one)==1, one_to_many.many_to_one)
        self.assert_('OneToMany' in complex.one_to_many, complex.one_to_many)
        self.assert_('Complex' in one_to_many.many_to_one, one_to_many.many_to_one)
    
    def test_register_N_M_parent_first(self):
        """
        Test registering a N:M related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        many_to_many = ModelWrapper(ManyToMany)
        self.manager.register(many_to_many)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_('ManyToMany' in complex.one_to_many, complex.one_to_many)
        self.assert_('Complex' in many_to_many.one_to_many, many_to_many.one_to_many)

    def test_register_N_M_parent_second(self):
        """
        Test registering a N:M related object
        """
        many_to_many = ModelWrapper(ManyToMany)
        self.manager.register(many_to_many)
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_('ManyToMany' in complex.one_to_many, complex.one_to_many)
        self.assert_('Complex' in many_to_many.one_to_many, many_to_many.one_to_many)
    
    def test_register_1_1_not_null(self):
        """
        Tests registering a 1:1 related object when the relationship can not be
        NULL but the other side of the relationship is not registered
        """
        pass
    
    def test_register_1_M_not_null(self):
        """
        Tests registering a 1:M related object when the relationship can not be
        NULL but the other side of the relationship is not registered
        """
        pass
        
    def test_register_N_M_not_null(self):
        """
        Tests registering a N:M related object when the relationship can not be
        NULL but the other side of the relationship is not registered
        """
        pass
    
    def test_register_extended_parent_first(self):
        """
        Test registering an object that is extended
        """
        extended = ModelWrapper(Extended)
        self.manager.register(extended)
        child = ModelWrapper(ChildA)
        self.manager.register(child)
        self.assert_(len(extended.children)==1, extended.children)
        self.assert_(len(child.parent)==1, child.parent)
        self.assert_('ChildA' in extended.children, extended.children)
        self.assert_('Extended' in child.parent, child.parent)
    
    def test_register_extended_parent_second(self):
        """
        Test registering an object that is extended
        """
        child = ModelWrapper(ChildA)
        self.manager.register(child)
        extended = ModelWrapper(Extended)
        self.manager.register(extended)
        self.assert_(len(extended.children)==1, extended.children)
        self.assert_(len(child.parent)==1, child.parent)
        self.assert_('ChildA' in extended.children, extended.children)
        self.assert_('Extended' in child.parent, child.parent)
    
    def test_register_child_parent_not_registered(self):
        """
        Test registering a child when the parent is not registered
        """
        pass
    
    def test_register_recursive(self):
        """
        Test registering a model with a recursive relationship
        """
        pass