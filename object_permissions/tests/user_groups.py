from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import Client

from object_permissions import register, grant, revoke, get_user_perms, \
    get_model_perms
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission


__all__ = ('TestUserGroups',)


class TestUserGroups(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        
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
    
    def test_view_detail(self):
        """
        Test Viewing the detail for an user_group
        
        Verifies:
            * 200 returned for valid user_group
            * 404 returned for invalid user_group
        """
        user = self.user
        group = self.test_save()
        c = Client()
        
        response = c.get('/user_group/%d' % group.id )
        self.assertEqual(200, response.status_code)
        
        response = c.get('/user_group/0')
        self.assertEqual(404, response.status_code)
    
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
        self.assertEqual('user_groups/add_user.html', response.template.name)
        
        # authorized post (superuser)
        revoke(user, 'admin', group)
        user.is_superuser = True
        user.save()
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('user_groups/add_user.html', response.template.name)
        
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
        self.assertEqual('user_groups/user_row.html', response.template.name)
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
        """
        user = self.user
        group = self.test_save()
        c = Client()
        group.users.add(user)
        
        # invalid permissions
        response = c.get('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        response = c.post('/user_group/%d/user/add/' % group.id)
        self.assertEqual(403, response.status_code)
        
        # authorize and login
        self.assert_(c.login(username=user.username, password='secret'))
        grant(user, 'admin', group)
        
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
            * POST without user id returns error as json
            * POST for invalid user id returns error as json
            * adding user a second time returns error as json
        """
        user = self.user
        group = self.test_save()
        group.users.add(user)
        
        register('Perm1', UserGroup)
        register('Perm2', UserGroup)
        
        c = Client()
        
        # unauthorized
        response = c.get('/user_group/%d/user/%s/' % (group.id, 0))
        self.assertEqual(403, response.status_code)
        response = c.post('/user_group/%d/user/%s/' % (group.id, 0))
        self.assertEqual(403, response.status_code)
        
        # authorized post (perm granted)
        grant(user, 'admin', group)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get('/user_group/%d/user/%s/' % (group.id, user.id))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('user_groups/permissions.html', response.template.name)
        
        # authorized post (superuser)
        revoke(user, 'admin', group)
        user.is_superuser = True
        user.save()
        
        response = c.get('/user_group/%d/user/%s/' % (group.id, user.id))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('user_groups/permissions.html', response.template.name)
        
        # invalid user
        response = c.post('/user_group/%d/user/%s/' % (group.id, 0))
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid permission
        data = {'permissions':['DoesNotExist']}
        response = c.post('/user_group/%d/user/%s/' % (group.id, user.id), data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid post
        data = {'permissions':['Perm1','Perm2']}
        response = c.post('/user_group/%d/user/%s/' % (group.id, user.id), data)
        self.assertEqual(200, response.status_code)
        
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('user_groups/user_row.html', response.template.name)
        self.assert_(user.has_perm('Perm1', group))
        self.assert_(user.has_perm('Perm2', group))
        self.assertEqual(['Perm1','Perm2'], get_user_perms(user, group))