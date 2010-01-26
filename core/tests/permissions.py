import unittest

from core.models import Permissable, Permission, Group, PermissionGroup
from core.util import if_in

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(Permissable_Test),
            unittest.TestLoader().loadTestsFromTestCase(Permission_Test),
            unittest.TestLoader().loadTestsFromTestCase(PermissionGroup_Test),
        ])


class Permissable_Test(unittest.TestCase):
    def setUp(self):
        self.user = Permissable()
        self.user.name = 'tester'
        self.user.save()
        self.a = Permission(path='one', level=1)
        self.a.granted_to = self.user
        self.a.save()
        self.b = Permission(path='two', level=2)
        self.b.granted_to = self.user
        self.b.save()
        
    def tearDown(self):
        Permission.objects.all().delete()
        Permissable.objects.all().delete()
    
    def test_load_permissions(self):
        perms = self.user.load_permissions()
        self.assert_('one' in perms)
        self.assert_('two' in perms)
        self.assert_(perms['one'][None]==1)
        self.assert_(perms['two'][None]==2)
        self.assert_(len(perms)==2)


class Permission_Test(unittest.TestCase):
    def setUp(self):        
        self.a = Permission(path='one', level=1)
        self.b = Permission(path='one', level=1)
        self.c = Permission(path='one', level=2)
        self.d = Permission(path='two', level=1)
        self.e = Permission(path='two', level=2)
        
    def test_gt(self):
        self.assertFalse(self.a>self.b)
        self.assertFalse(self.a>self.c)
        self.assertFalse(self.a>self.d)
        self.assertFalse(self.a>self.e)
        self.assertFalse(self.c>self.c)
        self.assertFalse(self.c>self.e)
        self.assert_(self.c>self.a)
        self.assert_(self.c>self.d)

    def test_ge(self):
        self.assert_(self.a >= self.b)
        self.assertFalse(self.a>=self.c)
        self.assert_(self.a>=self.d)
        self.assertFalse(self.a>=self.e)
        self.assert_(self.c>=self.c)
        self.assert_(self.c>=self.e)
        self.assert_(self.c>=self.a)
        self.assert_(self.c>=self.d)

    def test_lt(self):
        self.assertFalse(self.a<self.b)
        self.assert_(self.a<self.c)
        self.assertFalse(self.a<self.d)
        self.assert_(self.a<self.e)
        self.assertFalse(self.c<self.c)
        self.assertFalse(self.c<self.e)
        self.assertFalse(self.c<self.a)
        self.assertFalse(self.c<self.d)

    def test_le(self):
        self.assert_(self.a<=self.b)
        self.assert_(self.a<=self.c)
        self.assert_(self.a<=self.d)
        self.assert_(self.a<=self.e)
        self.assert_(self.c<=self.c)
        self.assert_(self.c<=self.e)
        self.assertFalse(self.c<=self.a)
        self.assertFalse(self.c<=self.d)

    def test_path_to_list(self):
        target, path = Permission.path_list('one')
        self.assert_(target=='one', target)
        self.assert_(path==None, path)
        target, path = Permission.path_list('one.two')
        self.assert_(target=='one', target)
        self.assert_(path==('two',), path)
        target, path = Permission.path_list('one.two.three')
        self.assert_(target=='one', target)
        self.assert_(path==('two','three'), path)


class PermissionGroup_Test(unittest.TestCase):
    def setUp(self):
        user = Permissable()
        user.name = 'tester'
        user.save()
        permA = Permission(path='one', level=1)
        permA.granted_to = user
        permA.save()
        permB = Permission(path='two', level=1)
        permB.granted_to = user
        permB.save()
        permC = Permission(path='four', level=2)
        permC.granted_to = user
        permC.save()
        permD = Permission(path='four.five.six', level=2)
        permD.granted_to = user
        permD.save()
        permE = Permission(path='five', level=2)
        permE.granted_to = user
        permE.save()
        groupA = PermissionGroup()
        groupA.name = 'GroupA'
        groupA.save()
        groupA.users.add(user)
        permGA = Permission(path='three', level=1)
        permGA.granted_to = groupA
        permGA.save()
        permGB = Permission(path='two', level=2)
        permGB.granted_to = groupA
        permGB.save()
        permGC = Permission(path='five.six', level=2)
        permGC.granted_to = user
        permGC.save()
        self.user = user
        
    def tearDown(self):
        Permission.objects.all().delete()
        Permissable.objects.all().delete()
        PermissionGroup.objects.all().delete()
    
    def test_load_permissions(self):
        """
        Tests basic permissions loading
        """
        perms = self.user.load_permissions()
        self.assert_(len(perms)==5)
        self.assert_('one' in perms, perms)
        self.assert_(perms['one'][None]==1)
        self.assert_('two' in perms)
        self.assert_(perms['two'][None]==1)
        self.assert_('three' in perms)
        self.assert_(perms['three'][None]==1)
        
    def test_load_permissions_duplicate_permissions(self):
        """
        Tests loading the same permission when it is directly on a permissable
        and on a group the permissable is a member of
        """
        raise Exception()

    def test_load_permissions_combine_target(self):
        """
        Tests loading permissions when multiple permissions for the same target
        are present
        """
        perms = self.user.load_permissions()
        self.assert_('four' in perms, perms)
        self.assert_(len(perms['four'])==2, perms['four'])
        self.assert_(None in perms['four'], perms['four'])
        self.assert_(('five','six') in perms['four'], perms['four'])
        
    def test_load_permissions_combine_target_from_group(self):
        """
        Tests loading permissions when multiple permissions for the same target
        are present as a result of some of those perms coming from a group
        """
        perms = self.user.load_permissions()
        self.assert_('five' in perms, perms)
        self.assert_(len(perms['five'])==2, perms['five'])
        self.assert_(None in perms['five'], perms['five'])
        self.assert_(('six',) in perms['five'], perms['five'])

