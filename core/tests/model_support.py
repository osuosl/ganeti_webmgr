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
            unittest.TestLoader().loadTestsFromTestCase(ModelWrapper_Test),
            unittest.TestLoader().loadTestsFromTestCase(ModelWrapper_Permissions_Test)
        ])

class ModelWrapper_Test(unittest.TestCase):
    def setUp(self):
        if not 'tests' in settings.INSTALLED_APPS:
            raise Exception('Test models are not installed tests cannot run')
        
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)
    
    def test_register_simple(self):
        simple= ModelWrapper(Simple)
        self.manager.register(simple)
        self.assert_('Simple' in self.manager, self.manager.enabled)
        self.assert_('value' in simple.fields, simple.fields)
        self.assert_(len(simple.fields)==1, simple.fields)
    
    def test_deregister_simple(self):
        simple= ModelWrapper(Simple)
        self.manager.register(simple)
        self.manager.deregister('Simple')
        self.assertFalse('Simple' in self.manager, self.manager.enabled)
    
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
    
    def test_deregister_complex_no_related_registered(self):
        """
        Tests deregistering an object with relations when none of the
        relations are registered
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.manager.deregister(complex)
        self.assertFalse('Complex' in self.manager, self.manager.enabled)
    
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
        self.assert_('onetoone' in complex.one_to_one, complex.one_to_one)
        self.assert_('complex' in one_to_one.one_to_one, one_to_one.one_to_one)
        
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
        self.assert_('onetoone' in complex.one_to_one, complex.one_to_one)
        self.assert_('complex' in one_to_one.one_to_one, one_to_one.one_to_one)
    
    def test_deregister_1_1_parent_first(self):
        """
        Test deregistering a 1:1 related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        one_to_one = ModelWrapper(OneToOne)
        self.manager.register(one_to_one)
        self.manager.deregister(complex)
        self.assert_(len(one_to_one.one_to_one)==0, one_to_one.one_to_one)
        self.assertFalse('complex' in one_to_one.one_to_one, one_to_one.one_to_one)
    
    def test_deregister_1_1_parent_second(self):
        """
        Test deregistering a 1:1 related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        one_to_one = ModelWrapper(OneToOne)
        self.manager.register(one_to_one)
        self.manager.deregister(one_to_one)
        self.assert_(len(complex.one_to_one)==0, complex.one_to_one)        
        self.assertFalse('onetoone' in complex.one_to_one, complex.one_to_one)
    
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
        self.assert_('one_to_manys' in complex.one_to_many, complex.one_to_many)
        self.assert_('complex' in one_to_many.many_to_one, one_to_many.many_to_one)
        
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
        self.assert_('one_to_manys' in complex.one_to_many, complex.one_to_many)
        self.assert_('complex' in one_to_many.many_to_one, one_to_many.many_to_one)
    
    def test_register_N_M_parent_first(self):
        """
        Test registering a N:M related object
        """
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        many_to_many = ModelWrapper(ManyToMany)
        self.manager.register(many_to_many)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_('many_to_manys' in complex.one_to_many, complex.one_to_many)
        self.assert_('complex' in many_to_many.one_to_many, many_to_many.one_to_many)

    def test_register_N_M_parent_second(self):
        """
        Test registering a N:M related object
        """
        many_to_many = ModelWrapper(ManyToMany)
        self.manager.register(many_to_many)
        complex = ModelWrapper(Complex)
        self.manager.register(complex)
        self.assert_(len(complex.one_to_many)==1, complex.one_to_many)
        self.assert_('many_to_manys' in complex.one_to_many, complex.one_to_many)
        self.assert_('complex' in many_to_many.one_to_many, many_to_many.one_to_many)
    
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
        self.assert_('childa' in extended.children, extended.children)
        self.assert_('extended_ptr' in child.parent, child.parent)
    
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
        self.assert_('childa' in extended.children, extended.children)
        self.assert_('extended_ptr' in child.parent, child.parent)
    
    def test_register_child_parent_not_registered(self):
        """
        Test registering a child when the parent is not registered
        """
        pass
    
    def test_register_recursive(self):
        """
        Test registering a model with a recursive relationship
        """
        recursive = ModelWrapper(Recursive)
        self.manager.register(recursive)
        self.assert_(len(recursive.many_to_one)==1, recursive.many_to_one)
        self.assert_(len(recursive.one_to_many)==1, recursive.one_to_many)
        self.assert_('parent' in recursive.many_to_one, recursive.many_to_one)
        self.assert_('children' in recursive.one_to_many, recursive.one_to_many)


class ModelWrapper_Permissions_Test(unittest.TestCase):
    """
    Tests permissions on a model
    """
    
    def setUp(self):
        # register models
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        manager.register(ModelWrapper(Permissable))
        manager.register(ModelWrapper(UserProfile))
        manager.register(ModelWrapper(Group))
        manager.register(ModelWrapper(Simple))
        manager.register(ModelWrapper(Complex))
        manager.register(ModelWrapper(OneToOne))
        manager.register(ModelWrapper(OneToMany))
        manager.register(ModelWrapper(MultipleParentsParentA))
        manager.register(ModelWrapper(MultipleParentsParentB))
        manager.register(ModelWrapper(MultipleParentsChild))
        manager.register(ModelWrapper(DepthTestRoot))
        manager.register(ModelWrapper(DepthTestLevel1))
        manager.register(ModelWrapper(DepthTestLevel2))
        
        user = UserProfile()
        user.name = 'tester'
        user.save()
        
        self.user = user
        self.manager = manager
    
    def tearDown(self):
        pass
    
    def test_permission_on_model(self):
        """
        Tests permissions directly on a model with no path involved:
           * user should have access to all instances of model
        """
        perm = Permission(mask=PERM_READ|PERM_WRITE,
                          path='Simple',
                          granted_to = self.user)
        perm.save()
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(self.user, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
    
    def test_permission_possess(self):
        """
        Tests permissions when using a possess filter to indicate perms already
        possessed by the user
            * should still return all perms requested
        """
        perm = Permission(mask=PERM_READ|PERM_WRITE,
                  path='Simple',
                  granted_to = self.user)
        perm.save()
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(self.user, 
                                                possess=PERM_READ|PERM_WRITE,
                                                id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(self.user, possess=PERM_READ,
                                                id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(self.user, possess=PERM_ALL, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assert_(mask&PERM_CREATE, bin(mask))
        self.assert_(mask&PERM_DELETE, bin(mask))
 
    def test_permission_mask(self):
        """
        Tests permissions when asking only for a specific subset of perms
           * must return perm requests, may return other perms as well
        """
        perm = Permission(mask=PERM_READ|PERM_WRITE,
                  path='Simple',
                  granted_to = self.user)
        perm.save()
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(self.user, mask=PERM_ALL,
                                                id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(self.user, mask=PERM_READ,
                                                id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(self.user,
                                                mask=PERM_READ|PERM_WRITE,
                                                id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
    
    def test_no_permission_on_model(self):
        """
        Tests permissions directly on a model with no path involved:
           * user should have access to all instances of model
        """
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(self.user, id=A.id)
        self.assertFalse(mask, bin(mask))
    
    def test_permissions_on_model_indirect(self):
        """
        Tests permissions on a model joined by a path:
           * user should have access to only instances owned by the head of the
             path
        """
        perm = Permission(mask=PERM_READ|PERM_WRITE, \
                          path='OneToOne.complex', \
                          granted_to=self.user)
        perm.save()
        complex = Complex()
        complex.save()
        A = OneToOne(complex=complex)        
        A.save()
        B = OneToOne()
        B.save()
        mask = self.manager['OneToOne'].has_perms(self.user, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(self.user, id=B.id)
        self.assert_(mask==PERM_NONE, bin(mask))
    
    def test_permissions_on_model_indirect_indirect(self):
        """
        Tests permissions on a model joined by a path with more than 2 models:
           * user should have access to only instances owned by the head of the
             path
        """
        perm = Permission(mask=PERM_READ|PERM_WRITE, \
                          path='DepthTestLevel2.parent.parent', \
                          granted_to=self.user)
        perm.save()
        root = DepthTestRoot()
        root.save()
        L1A = DepthTestLevel1(parent=root)
        L1A.save()
        L1B = DepthTestLevel1()
        L1B.save()
        L2A = DepthTestLevel2(parent=L1A)
        L2A.save()
        L2B = DepthTestLevel2(parent=L1B)
        L2B.save()
        L2C = DepthTestLevel2()
        L2C.save()
        mask = self.manager['DepthTestLevel2'].has_perms(self.user, id=L2A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['DepthTestLevel2'].has_perms(self.user, id=L2B.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['DepthTestLevel2'].has_perms(self.user, id=L2C.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['DepthTestLevel1'].has_perms(self.user, id=L1A.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['DepthTestLevel1'].has_perms(self.user, id=L1B.id)
        self.assert_(mask==PERM_NONE, bin(mask))
    
    def test_permissions_combined_from_groups(self):
        """
        Tests permissions when user has two groups with different permission
        levels on the same model:
            * user should receive combination of masks from both groups
        """
        group = Group()
        group.save()
        self.user.groups.add(group)
        perm = Permission(mask=PERM_READ, \
                          path='Simple', \
                          granted_to=self.user)
        perm.save()
        perm = Permission(mask=PERM_WRITE, \
                          path='Simple', \
                          granted_to=group)
        perm.save()
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(self.user, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
    
    def test_permissions_combined_from_groups_different_ownership_path(self):
        """
        Tests permissions when user has two groups with different permission
        levels on the same model, but from different paths:
            * on models targeted by both paths: culmulative permissions
            * on models targeted by one path: perm from just that group
        """
        groupA = Group()
        groupA.save()
        groupB = Group()
        groupB.save()
        self.user.groups.add(groupA)
        self.user.groups.add(groupB)
        perm = Permission(mask=PERM_READ, \
                          path='MultipleParentsChild.parent_a', \
                          granted_to=groupA)
        perm.save()
        perm = Permission(mask=PERM_WRITE, \
                          path='MultipleParentsChild.parent_b', \
                          granted_to=groupB)
        perm.save()
        parent_a = MultipleParentsParentA()
        parent_a.save()
        parent_b = MultipleParentsParentB()
        parent_b.save()
        A = MultipleParentsChild(parent_a=parent_a)
        A.save()
        B = MultipleParentsChild(parent_b=parent_b)
        B.save()
        C = MultipleParentsChild(parent_a=parent_a, parent_b=parent_b)
        C.save()
        D = MultipleParentsChild()
        D.save()
        mask = self.manager['MultipleParentsChild'].has_perms(self.user, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assertFalse(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['MultipleParentsChild'].has_perms(self.user, id=B.id)
        self.assertFalse(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['MultipleParentsChild'].has_perms(self.user, id=C.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['MultipleParentsChild'].has_perms(self.user, id=D.id)
        self.assert_(mask==PERM_NONE, bin(mask))
    
    def test_ownership_directly(self):
        """
        Tests ownership of a model directly related to model
            * user should only have access to instances of the model it owns
        """
        groupA = Group()
        groupA.save()
        groupB = Group()
        groupB.save()
        perm = Permission(mask=PERM_READ, \
                          path='Simple.owner.1', \
                          granted_to=groupA)
        perm.save()
        perm = Permission(mask=PERM_WRITE, \
                          path='Simple.owner.1', \
                          granted_to=groupB)
        perm.save()
        A = Simple(owner=groupA)
        A.save()
        B = Simple(owner=groupB)
        B.save()
        C = Simple()
        C.save()
        mask = self.manager['Simple'].has_perms(groupA, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assertFalse(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(groupA, id=B.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['Simple'].has_perms(groupA, id=C.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['Simple'].has_perms(groupB, id=A.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['Simple'].has_perms(groupB, id=B.id)
        self.assertFalse(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['Simple'].has_perms(groupB, id=C.id)
        self.assert_(mask==PERM_NONE, bin(mask))
    
    def test_ownership_indirectly(self):
        """
        Tests ownership of a model indirectly related to model through another
        model.
            * user should only have access to instances that are owned by
              instances it owns.
        """
        groupA = Group()
        groupA.save()
        groupB = Group()
        groupB.save()
        perm = Permission(mask=PERM_READ, \
                          path='OneToOne.complex.owner.1', \
                          granted_to=groupA)
        perm.save()
        perm = Permission(mask=PERM_WRITE, \
                          path='OneToOne.complex.owner.1', \
                          granted_to=groupB)
        perm.save()
        CA = Complex(owner=groupA)
        CA.save()
        CB = Complex(owner=groupB)
        CB.save()
        CC = Complex()
        CC.save()
        A = OneToOne(complex=CA)
        A.save()
        B = OneToOne(complex=CB)
        B.save()
        C = OneToOne(complex=CC)
        C.save()
        D = OneToOne()
        D.save()
        mask = self.manager['OneToOne'].has_perms(groupA, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assertFalse(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupA, id=B.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupA, id=C.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupA, id=D.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupB, id=A.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupB, id=B.id)
        self.assertFalse(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupB, id=C.id)
        self.assert_(mask==PERM_NONE, bin(mask))
        mask = self.manager['OneToOne'].has_perms(groupB, id=D.id)
        self.assert_(mask==PERM_NONE, bin(mask))
    
    def test_permission_on_group_using_group(self):
        """
        Tests permission granted to a group by passing in the group rather
        than the user to check perms:
            * group should have granted perms
        """
        group = Group()
        group.save()
        perm = Permission(mask=PERM_READ|PERM_WRITE, \
                          path='Simple', \
                          granted_to=group)
        perm.save()
        A = Simple()
        A.save()
        mask = self.manager['Simple'].has_perms(group, id=A.id)
        self.assert_(mask&PERM_READ, bin(mask))
        self.assert_(mask&PERM_WRITE, bin(mask))
        self.assertFalse(mask&PERM_CREATE, bin(mask))
        self.assertFalse(mask&PERM_DELETE, bin(mask))