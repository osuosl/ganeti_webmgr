from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission


__all__ = ('TestUserGroups','TestUserGroupViews')


class TestUserGroups(TestCase):
    perms = [u'Perm1', u'Perm2', u'Perm3', u'Perm4']
    
    def setUp(self):
        self.tearDown()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()
        
        
        self.object0 = Group.objects.create(name='test0')
        self.object0.save()
        self.object1 = Group.objects.create(name='test1')
        self.object1.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', UserGroup)
    
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        UserGroup.objects.all().delete()
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        ObjectPermissionType.objects.all().delete()
        
    def test_trivial(self):
        """ Test instantiating a UserGroup """
        group = UserGroup()
        perm = GroupObjectPermission()
    
    def test_model(self):
        """
        Test model constraints
        
        Verifies:
            * group name is unique
            * Granted Permissions must be unique to UserGroup/object combinations
        """
        user = self.user
        object = self.object0
        ct = ContentType.objects.get_for_model(object)
        
        pt = ObjectPermissionType(name='Perm1', content_type=ct)
        pt.save()
        
        group = UserGroup(name='TestGroup')
        group.save()
        
        GroupObjectPermission(group=group, object_id=object.id, permission=pt).save()
        
        try:
            UserGroup(name='TestGroup').save()
            self.fail('Integrity Error not raised for duplicate UserGroup')
        except IntegrityError:
            pass
        
        try:
            GroupObjectPermission(group=group, object_id=object.id, permission=pt).save()
            self.fail('Integrity Error not raised for duplicate GroupObjectPermission')
        except IntegrityError:
            pass

    def test_save(self, name='test'):
        """ Test saving an UserGroup """
        group = UserGroup(name=name)
        group.save()
        return group
    
    def test_permissions(self):
        """ Verify all model perms are created """
        self.assertEqual(['admin'], get_model_perms(UserGroup))
    
    def test_grant_group_permissions(self):
        """
        Test granting permissions to a UserGroup
       
        Verifies:
            * granted properties are available via backend (has_perm)
            * granted properties are only granted to the specified user, object
              combinations
            * granting unknown permission raises error
        """
        user0 = self.user
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        group0 = UserGroup(name='TestGroup0')
        group0.save()
        group0.users.add(user0)
        
        group1 = UserGroup(name='TestGroup1')
        group1.save()
        group1.users.add(user1)
        
        for perm in self.perms:
            register(perm, Group)
        
        # grant single property
        group0.grant('Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant property again
        group0.grant('Perm1', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        
        # grant second property
        group0.grant('Perm2', object0)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assertFalse(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant property to another object
        group0.grant('Perm2', object1)
        self.assert_(user0.has_perm('Perm1', object0))
        self.assertFalse(user0.has_perm('Perm1', object1))
        self.assertFalse(user1.has_perm('Perm1', object0))
        self.assertFalse(user1.has_perm('Perm1', object1))
        self.assert_(user0.has_perm('Perm2', object0))
        self.assert_(user0.has_perm('Perm2', object1))
        self.assertFalse(user1.has_perm('Perm2', object0))
        self.assertFalse(user1.has_perm('Perm2', object1))
        
        # grant perms to other user
        group1.grant('Perm3', object0)
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
            group1.grant('UnknownPerm', object0)
        self.assertRaises(ObjectPermissionType.DoesNotExist, grant_unknown)
    
    def test_revoke_group_permissions(self):
        """
        Test revoking permissions from UserGroups
        
        Verifies:
            * revoked properties are removed
            * revoked properties are only removed from the correct UserGroup/obj combinations
            * revoking property UserGroup does not have does not give an error
            * revoking unknown permission raises error
        """
        user0 = self.user
        user1 = self.user1
        object0 = self.object0
        object1 = self.object1
        
        group0 = self.test_save(name='TestGroup0')
        group0.users.add(user0)
        
        group1 = self.test_save(name='TestGroup1')
        group1.users.add(user1)
        perms = self.perms
        
        for perm in perms:
            register(perm, Group)
            group0.grant(perm, object0)
            group0.grant(perm, object1)
            group1.grant(perm, object0)
            group1.grant(perm, object1)
        
        # revoke single perm
        group0.revoke('Perm1', object0)
        self.assertEqual([u'Perm2', u'Perm3', u'Perm4'], group0.get_perms(object0))
        self.assertEqual(perms, group0.get_perms(object1))
        self.assertEqual(perms, group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
        
        # revoke a second perm
        group0.revoke('Perm3', object0)
        self.assertEqual([u'Perm2', u'Perm4'], group0.get_perms(object0))
        self.assertEqual(perms, group0.get_perms(object1))
        self.assertEqual(perms, group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
        
        # revoke from another object
        group0.revoke('Perm3', object1)
        self.assertEqual([u'Perm2', u'Perm4'], group0.get_perms(object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], group0.get_perms(object1))
        self.assertEqual(perms, group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
        
        # revoke from another user
        group1.revoke('Perm4', object0)
        self.assertEqual([u'Perm2', u'Perm4'], group0.get_perms(object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], group0.get_perms(object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
        
        # revoke perm user does not have
        group0.revoke('Perm1', object0)
        self.assertEqual([u'Perm2', u'Perm4'], group0.get_perms(object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], group0.get_perms(object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
        
        # revoke perm that does not exist
        group0.revoke('DoesNotExist', object0)
        self.assertEqual([u'Perm2', u'Perm4'], group0.get_perms(object0))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm4'], group0.get_perms(object1))
        self.assertEqual([u'Perm1', u'Perm2', u'Perm3'], group1.get_perms(object0))
        self.assertEqual(perms, group1.get_perms(object1))
    
    def test_revoke_all_group(self):
        """
        Test revoking all permissions from a group
        
        Verifies
            * revoked properties are only removed from the correct user/obj combinations
            * revoking property user does not have does not give an error
            * revoking unknown permission raises error
        """
        user0 = self.user
        user1 = self.user1
        group0 = self.test_save(name='TestGroup0')
        group1 = self.test_save(name='TestGroup1')
        object0 = self.object0
        object1 = self.object1
        perms = self.perms
        
        for perm in perms:
            register(perm, Group)
            grant_group(group0, perm, object0)
            grant_group(group0, perm, object1)
            grant_group(group1, perm, object0)
            grant_group(group1, perm, object1)
        
        revoke_all_group(group0, object0)
        self.assertEqual([], get_group_perms(group0, object0))
        self.assertEqual(perms, get_group_perms(group0, object1))
        self.assertEqual(perms, get_group_perms(group1, object0))
        self.assertEqual(perms, get_group_perms(group1, object1))
        
        revoke_all_group(group0, object1)
        self.assertEqual([], get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual(perms, get_group_perms(group1, object0))
        self.assertEqual(perms, get_group_perms(group1, object1))
        
        revoke_all_group(group1, object0)
        self.assertEqual([], get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        self.assertEqual(perms, get_group_perms(group1, object1))
        
        revoke_all_group(group1, object1)
        self.assertEqual([], get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        self.assertEqual([], get_group_perms(group1, object1))
    
    def test_set_perms(self):
        """
        Test setting perms to an exact set
        """
        group0 = self.test_save(name='TestGroup0')
        group1 = self.test_save(name='TestGroup1')
        object0 = self.object0
        object1 = self.object1
        
        perms1 = self.perms
        perms2 = ['Perm1', 'Perm2']
        perms3 = ['Perm2', 'Perm3']
        perms4 = []
        
        for perm in self.perms:
            register(perm, Group)
        # grant single property
        set_group_perms(group0, perms1, object0)
        self.assertEqual(perms1, get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        
        set_group_perms(group0, perms2, object0)
        self.assertEqual(perms2, get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        
        set_group_perms(group0, perms3, object0)
        self.assertEqual(perms3, get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        
        set_group_perms(group0, perms4, object0)
        self.assertEqual(perms4, get_group_perms(group0, object0))
        self.assertEqual([], get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        
        set_group_perms(group0, perms2, object1)
        self.assertEqual(perms4, get_group_perms(group0, object0))
        self.assertEqual(perms2, get_group_perms(group0, object1))
        self.assertEqual([], get_group_perms(group1, object0))
        
        set_group_perms(group1, perms1, object0)
        self.assertEqual(perms4, get_group_perms(group0, object0))
        self.assertEqual(perms2, get_group_perms(group0, object1))
        self.assertEqual(perms1, get_group_perms(group1, object0))
    
    def test_has_perm(self):
        """
        Additional tests for has_perms
        
        Verifies:
            * None object always returns false
            * Nonexistent perm returns false
            * Perm user does not possess returns false
        """
        user = self.user
        group = UserGroup(name='TestGroup')
        group.save()
        group.users.add(user)
        object = self.object0
        
        for perm in self.perms:
            register(perm, Group)
        group.grant('Perm1', object)
        
        self.assertTrue(user.has_perm('Perm1', object))
        self.assertFalse(user.has_perm('Perm1', None))
        self.assertFalse(user.has_perm('DoesNotExist'), object)
        self.assertFalse(user.has_perm('Perm2', object))
    
    def test_get_groups(self):
        """
        Tests retrieving list of UserGroups with perms on an object
        """
        group0 = UserGroup(name='TestGroup0')
        group0.save()
        group1 = UserGroup(name='TestGroup1')
        group1.save()
        object0 = self.object0
        object1 = self.object1
        
        for perm in self.perms:
            register(perm, Group)
        group0.grant('Perm1', object0)
        group0.grant('Perm3', object1)
        group1.grant('Perm2', object1)
        
        self.assert_(group0 in get_groups(object0))
        self.assertFalse(group1 in get_groups(object0))
        self.assert_(group0 in get_groups(object1))
        self.assert_(group1 in get_groups(object1))
        self.assert_(len(get_groups(object1))==2)
    
class TestUserGroupViews(TestCase):
    perms = [u'Perm1', u'Perm2', u'Perm3', u'Perm4']
    
    def setUp(self):
        self.tearDown()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()
        
        
        self.object0 = Group.objects.create(name='test0')
        self.object0.save()
        self.object1 = Group.objects.create(name='test1')
        self.object1.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', UserGroup)
    
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        UserGroup.objects.all().delete()
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        ObjectPermissionType.objects.all().delete()
    
    def test_save(self, name='test'):
        """ Test saving an UserGroup """
        group = UserGroup(name=name)
        group.save()
        return group
    
    def test_view_list(self):
        """
        Test viewing list of UserGroups
        """
        user = self.user
        group = self.test_save()
        c = Client()
        url = '/user_groups/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        
        # authorized (permission)
        # XXX need to implement permissions system for subset of UserGroups
        # grant(user, '')
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(200, response.status_code)
        # self.assertEquals('text/html; charset=utf-8', response['content-type'])
        # self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/list.html')
    
    def test_view_detail(self):
        """
        Test Viewing the detail for a UserGroup
        
        Verifies:
            * 200 returned for valid user_group
            * 404 returned for invalid user_group
        """
        user = self.user
        group = self.test_save()
        c = Client()
        url = '/user_group/%s/'
        
        # anonymous user
        response = c.get(url % group.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # invalid usergroup
        response = c.get(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', group)
        response = c.get(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/detail.html')
        
        # authorized (superuser)
        response = c.get(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/detail.html')

    def test_view_edit(self):
        user = self.user
        group = self.test_save()
        c = Client()
        url = '/user_group/%s/'
        
        # anonymous user
        response = c.post(url % group.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url % group.id)
        self.assertEqual(403, response.status_code)
        
        # invalid usergroup
        response = c.post(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)
        
        # get form - authorized (permission)
        # XXX need to implement Class wide permission for creating editing groups
        #grant(user, 'admin', group)
        #response = c.post(url % group.id)
        #self.assertEqual(200, response.status_code)
        #self.assertEquals('text/html; charset=utf-8', response['content-type'])
        #self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # get form - authorized (permission)
        grant(user, 'admin', group)
        response = c.post(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # get form - authorized (superuser)
        user.revoke('admin', group)
        user.is_superuser = True
        user.save()
        response = c.post(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # missing name
        data = {'id':group.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # successful edit
        data = {'id':group.id, 'name':'EDITED_NAME'}
        response = c.post(url % group.id, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/group_row.html')
        group = UserGroup.objects.get(id=group.id)
        self.assertEqual('EDITED_NAME', group.name)
    
    def test_view_create(self):
        """
        Test creating a new UserGroup
        """
        user = self.user
        group = self.test_save()
        c = Client()
        url = '/user_group/'
        
        # anonymous user
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url)
        self.assertEqual(403, response.status_code)
        
        # get form - authorized (permission)
        # XXX need to implement Class level permissions
        #grant(user, 'admin', group)
        #response = c.post(url % group.id)
        #self.assertEqual(200, response.status_code)
        #self.assertEquals('text/html; charset=utf-8', response['content-type'])
        #self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # get form - authorized (superuser)
        user.revoke('admin', group)
        user.is_superuser = True
        user.save()
        response = c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # missing name
        data = {'id':group.id}
        response = c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/edit.html')
        
        # successful edit
        data = {'name':'ADD_NEW_GROUP'}
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/group_row.html')
        self.assert_(UserGroup.objects.filter(name='ADD_NEW_GROUP').exists())
    
    def test_view_delete(self):
        """
        Test deleting a usergroup
        
        Verifies:
            * group is deleted
            * all associated permissions are deleted
        """
        user = self.user
        group0 = self.test_save()
        group1 = self.test_save(name='test2')
        c = Client()
        url = '/user_group/%s/'
        
        # anonymous user
        response = c.delete(url % group0.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.delete(url % group0.id)
        self.assertEqual(403, response.status_code)
        
        # invalid usergroup
        response = c.delete(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)
        
        # get form - authorized (permission)
        grant(user, 'admin', group0)
        response = c.delete(url % group0.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(UserGroup.objects.filter(id=group0.id).exists())
        self.assertEqual('1', response.content)
        
        # get form - authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.delete(url % group1.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(UserGroup.objects.filter(id=group1.id).exists())
        self.assertEqual('1', response.content)
    
    def test_view_add_user(self):
        """
        Test view for adding a user:
        
        Verifies:
            * request from unauthorized user results in 403
            * GET returns a 200 code, response is html
            * POST with a user id adds user, response is html for user
            * POST without user id returns error as json
            * POST for invalid user id returns error as json
            * adding user a second time returns error as json
        """
        user = self.user
        group = self.test_save()
        c = Client()
        
        # unauthorized
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        response = c.post('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        
        # authorized post (perm granted)
        grant(user, 'admin', group)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/add_user.html')
        
        # authorized post (superuser)
        revoke(user, 'admin', group)
        user.is_superuser = True
        user.save()
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/add_user.html')
        
        # missing user id
        response = c.post('/user_group/%d/user/add/' % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid user
        response = c.post('/user_group/%d/user/add/' % group.id, {'user':0})
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid post
        data = {'user':user.id}
        response = c.post('/user_group/%d/user/add/' % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('user_group/user_row.html', response.template.name)
        self.assert_(group.users.filter(id=user.id).exists())
        
        # same user again
        response = c.post('/user_group/%d/user/add/' % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals(group.users.filter(id=user.id).count(), 1)
    
    def test_view_remove_user(self):
        """
        Test view for adding a user:
        
        Verifies:
            * GET redirects user to 405
            * POST with a user id remove user, returns 1
            * POST without user id returns error as json
            * users lacking perms receive 403
            * removing user not in group returns error as json
            * removing user that does not exist returns error as json
            * user loses all permissions when removed from group
        """
        user = self.user
        group = self.test_save()
        c = Client()
        group.users.add(user)
        register('Perm1', UserGroup)
        
        # invalid permissions
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        response = c.post('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        
        # authorize and login
        self.assert_(c.login(username=user.username, password='secret'))
        grant(user, 'admin', group)
        grant(user, 'Perm1', group)
        
        # invalid method
        response = c.get('/user_group/%d/user/remove/' % group.id)
        self.assertEqual(405, response.status_code)
        
        # valid request (perm)
        data = {'user':user.id}
        response = c.post('/user_group/%d/user/remove/' % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(group.users.filter(id=user.id).exists())
        self.assertEqual([], user.get_perms(group))
        
        # valid request (superuser)
        revoke(user, 'admin', group)
        user.is_superuser = True
        user.save()
        group.users.add(user)
        response = c.post('/user_group/%d/user/remove/' % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(group.users.filter(id=user.id).exists())
        
        # remove user again
        response = c.post('/user_group/%d/user/remove/' % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(group.users.filter(id=user.id).exists())
        self.assertNotEqual('1', response.content)
        
        # remove invalid user
        response = c.post('/user_group/%d/user/remove/' % group.id, {'user':0})
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('1', response.content)
    
    def test_view_update_permissions(self):
        """
        Tests setting permissions for a user
        
        Verifies:
            * request from unauthorized user results in 403
            * GET returns a 200 code, response is html
            * POST with a user id adds user, response is html for user
            * POST without user_id or group_id returns error as json
            * POST with both a user_id and group_id returns error as json
            * POST for invalid user id returns error as json
            * POST for invalid group_id returns error as json
            * adding user a second time returns error as json
            * POST with a user_id adds user, response is html for user
            * POST with a group_id adds user, response is html for user
            * perms added to appropriate models
        """
        user = self.user
        group = self.test_save()
        group.users.add(user)
        group1 = self.test_save('other_group')
        
        register('Perm1', UserGroup)
        register('Perm2', UserGroup)
        
        c = Client()
        url = '/user_group/%d/user/'
        
        # unauthorized
        response = c.get(url % group.id)
        self.assertEqual(403, response.status_code)
        response = c.post(url % group.id)
        self.assertEqual(403, response.status_code)
        
        # authorized post (perm granted)
        grant(user, 'admin', group)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % group.id, {'user':user.id})
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/permissions.html')
        
        # authorized post (superuser)
        revoke(user, 'admin', group)
        user.is_superuser = True
        user.save()
        response = c.get(url % group.id, {'user':user.id})
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/permissions.html')
    
        # invalid user (GET)
        response = c.get(url % group.id, {'user':-1})
        self.assertEqual(404, response.status_code)
        
        # invalid group (GET)
        response = c.get(url % group.id, {'group':-1})
        self.assertEqual(404, response.status_code)
        
        # invalid user (POST)
        data = {'permissions':['Perm1'], 'user':-1}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid group (POST)
        data = {'permissions':['Perm1'], 'group':-1}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # no user or group (GET)
        data = {'permissions':['Perm1'], }
        response = c.get(url % group.id, data)
        self.assertEqual(404, response.status_code)
        
        # no user or group (POST)
        data = {'permissions':['Perm1'], }
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # user and group (POST)
        data = {'permissions':['Perm1'], 'user':user.id, 'group':group1.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid permission
        data = {'permissions':['DoesNotExist'], 'user':user.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid post user
        data = {'permissions':['Perm1','Perm2'], 'user':user.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/user_row.html')
        self.assert_(user.has_perm('Perm1', group))
        self.assert_(user.has_perm('Perm2', group))
        self.assertEqual(['Perm1','Perm2'], get_user_perms(user, group))
        
        # valid post no permissions user
        data = {'permissions':[], 'user':user.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], get_user_perms(user, group))
        
        # valid post group
        data = {'permissions':['Perm1','Perm2'], 'group':group1.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'user_group/user_row.html')
        self.assertEqual(['Perm1','Perm2'], group1.get_perms(group))
        
        # valid post no permissions group
        data = {'permissions':[], 'group':group1.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], group1.get_perms(group))