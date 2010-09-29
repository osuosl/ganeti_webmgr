from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType


from object_permissions import register, grant, revoke, get_user_perms, \
    get_model_perms
from models import ObjectPermission, ObjectPermissionType


class TestModelPermissions(TestCase):
    perms = [u'Perm1', u'Perm2', u'Perm3', u'Perm4']

    def setUp(self):
        self.tearDown()
        self.user0 = User(username='tester')
        self.user0.save()
        self.user1 = User(username='tester2')
        self.user1.save()
        
        self.object0 = Group.objects.create(name='test0')
        self.object0.save()
        self.object1 = Group.objects.create(name='test1')
        self.object1.save()
    
    def tearDown(self):
        Group.objects.all().delete()
        User.objects.all().delete()
        ObjectPermission.objects.all().delete()
        ObjectPermissionType.objects.all().delete()

    def test_register(self):
        """
        Tests registering a permission
        
        Verifies:
            * registering permission creates perm
            * registering a second time does nothing
            * registering additional perms creates them
        """
        register('Perm1', Group)
        ct = ContentType.objects.get_for_model(Group)
        self.assertEquals([u'Perm1'], get_model_perms(Group))
        
        register('Perm1', Group)
        self.assertEquals([u'Perm1'], get_model_perms(Group))
        
        register('Perm2', Group)
        register('Perm3', Group)
        register('Perm4', Group)
        self.assertEqual(self.perms, get_model_perms(Group))
    
    def test_grant_user_permissions(self):
        """
        Grant a user permissions
        
        Verifies:
            * granted properties are available via backend (has_perm)
            * granted properties are only granted to the specified user, object
              combinations
            * granting unknown permission raises error
        """
        user0 = self.user0
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        for perm in self.perms:
            register(perm, Group)
        
        # grant single property
        grant(user0, 'Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant property again
        grant(user0, 'Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant second property
        grant(user0, 'Perm2', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assertFalse(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant property to another object
        grant(user0, 'Perm2', object1)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assert_(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant perms to other user
        grant(user1, 'Perm3', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assert_(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        self.assert_(user1.has_perm('Perm3', object0))
        
        def grant_unknown():
            grant(user1, 'UnknownPerm', object0)
        self.assertRaises(ObjectPermissionType.DoesNotExist, grant_unknown)
    
    
    def test_revoke_user_permissions(self):
        """
        Test revoking permissions from users
        """
        user0 = self.user0
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        for perm in self.perms:
            register(perm, Group)
            grant(user0, perm, object0)
            grant(user0, perm, object1)
            grant(user1, perm, object0)
            grant(user1, perm, object1)

    
    def test_get_user_permissions(self):
        user0 = self.user0
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        for perm in self.perms:
            register(perm, Group)
        
        # grant single property
        grant(user0, 'Perm1', object0)
        self.assertEqual([u'Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property again
        grant(user0, 'Perm1', object0)
        self.assertEqual([u'Perm1'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant second property
        grant(user0, 'Perm2', object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant property to another object
        grant(user0, 'Perm2', object1)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm2'], get_user_perms(user0, object1))
        self.assertEqual([], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
        
        # grant perms to other user
        grant(user1, 'Perm3', object0)
        self.assertEqual([u'Perm1', u'Perm2'], get_user_perms(user0, object0))
        self.assertEqual([u'Perm2'], get_user_perms(user0, object1))
        self.assertEqual([u'Perm3'], get_user_perms(user1, object0))
        self.assertEqual([], get_user_perms(user1, object1))
    