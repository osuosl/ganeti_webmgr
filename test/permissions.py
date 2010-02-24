import unittest

from muddle.models import Permissable, Permission, Group, PermissionGroup
from muddle.plugins.registerable import PERM_READ, PERM_WRITE, PERM_CREATE, \
    PERM_DELETE, PERM_ALL, PERM_NONE

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
        self.a = Permission(path='one', mask=PERM_READ)
        self.a.granted_to = self.user
        self.a.save()
        self.b = Permission(path='two', mask=PERM_WRITE)
        self.b.granted_to = self.user
        self.b.save()
        
    def tearDown(self):
        Permission.objects.all().delete()
        Permissable.objects.all().delete()
    
    def test_load_permissions(self):
        perms = self.user.load_permissions()
        self.assert_('one' in perms)
        self.assert_('two' in perms)
        self.assert_(perms['one'][None]==PERM_READ)
        self.assert_(perms['two'][None]==PERM_WRITE)
        self.assert_(len(perms)==2)


class Permission_Test(unittest.TestCase):
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
        permA = Permission(path='one', mask=PERM_READ)
        permA.granted_to = user
        permA.save()
        permB = Permission(path='two', mask=PERM_READ)
        permB.granted_to = user
        permB.save()
        permC = Permission(path='four', mask=PERM_WRITE)
        permC.granted_to = user
        permC.save()
        permD = Permission(path='four.five.six', mask=PERM_WRITE)
        permD.granted_to = user
        permD.save()
        permE = Permission(path='five', mask=PERM_WRITE)
        permE.granted_to = user
        permE.save()
        permF = Permission(path='six', mask=PERM_READ)
        permF.granted_to = user
        permF.save()
        permG = Permission(path='six', mask=PERM_WRITE)
        permG.granted_to = user
        permG.save()
        groupA = PermissionGroup()
        groupA.name = 'GroupA'
        groupA.save()
        groupA.users.add(user)
        permGA = Permission(path='three', mask=PERM_READ)
        permGA.granted_to = groupA
        permGA.save()
        permGB = Permission(path='two', mask=PERM_WRITE)
        permGB.granted_to = groupA
        permGB.save()
        permGC = Permission(path='five.six', mask=PERM_WRITE)
        permGC.granted_to = user
        permGC.save()
        self.user = user
        
    def tearDown(self):
        Permission.objects.all().delete()
        Permissable.objects.all().delete()
        PermissionGroup.objects.all().delete()
    
    def test_load_permissions(self):
        """
        Tests basic permissions loading:
          * There should be 6 permission targets
          * Permissions for basic permissions should be set properly
        """
        perms = self.user.load_permissions()
        # verify how many were loaded
        self.assert_(len(perms)==6)
        # verify a single perm can be loaded
        self.assert_('one' in perms, perms)
        self.assert_(perms['one'][None]==PERM_READ)
        
        self.assert_('three' in perms)
        self.assert_(perms['three'][None]==PERM_READ)
        
    def test_load_permission_combine_masks(self):
        """
        tests combining masks for a target from a Permission and PermissionGroup
          * permissions mask should be the combination of both permissions
        """
        perms = self.user.load_permissions()
        self.assert_('two' in perms)
        mask = PERM_READ|PERM_WRITE
        self.assert_(perms['two'][None]==mask, (perms['two'][None], mask))
        
    def test_load_permissions_duplicate_permissions(self):
        """
        Tests loading the same permission is added twice for the same user.
        """
        perms = self.user.load_permissions()
        self.assert_('six' in perms)
        mask = PERM_READ|PERM_WRITE
        self.assert_(perms['six'][None]==mask, (perms['six'][None], mask))

    def test_load_permissions_combine_target(self):
        """
        Tests loading permissions when multiple permissions for the same target
        are present
          * all permission paths should exist in the targets dictionary
        """
        perms = self.user.load_permissions()
        self.assert_('four' in perms, perms)
        self.assert_(len(perms['four'])==2, perms['four'])
        self.assert_(None in perms['four'], perms['four'])
        self.assert_(('five','six') in perms['four'], perms['four'])
        
    def test_load_permissions_combine_target_from_group(self):
        """
        Tests loading permissions when multiple permissions for the same target
        are present as a result of some of those perms coming from a group:
           * all permission paths should exist in the targets dictionary
        """
        perms = self.user.load_permissions()
        self.assert_('five' in perms, perms)
        self.assert_(len(perms['five'])==2, perms['five'])
        self.assert_(None in perms['five'], perms['five'])
        self.assert_(('six',) in perms['five'], perms['five'])

