from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import register, grant, revoke, get_user_perms, \
    get_model_perms
from object_permissions.models import ObjectPermission

from ganeti.models import Organization


__all__ = ('TestOrganizations',)


class TestOrganizations(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Organization)
    
    def tearDown(self):
        User.objects.all().delete()
        Organization.objects.all().delete()
        ObjectPermission.objects.all().delete()
        
    def test_trivial(self):
        """ Test instantiating an Organization """
        org = Organization()
    
    def test_save(self, name='test'):
        """ Test saving an Organization """
        org = Organization(name=name)
        org.save()
        return org
    
    def test_permissions(self):
        """ Verify all model perms are created """
        self.assertEqual(['admin'], get_model_perms(Organization))
    
    def test_view_detail(self):
        """
        Test Viewing the detail for an organization
        
        Verifies:
            * 200 returned for valid organization
            * 404 returned for invalid organization
        """
        user = self.user
        org = self.test_save()
        c = Client()
        
        response = c.get('/organization/%d' % org.id )
        self.assertEqual(200, response.status_code)
        
        response = c.get('/organization/0')
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
        org = self.test_save()
        c = Client()
        
        # unauthorized
        response = c.get('/organization/%d/user/add/' % org.id)
        self.assertEqual(403, response.status_code)
        response = c.post('/organization/%d/user/add/' % org.id)
        self.assertEqual(403, response.status_code)
        
        # authorized post (perm granted)
        grant(user, 'admin', org)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get('/organization/%d/user/add/' % org.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/add_user.html', response.template.name)
        
        # authorized post (superuser)
        revoke(user, 'admin', org)
        user.is_superuser = True
        user.save()
        response = c.get('/organization/%d/user/add/' % org.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/add_user.html', response.template.name)
        
        # missing user id
        response = c.post('/organization/%d/user/add/' % org.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid user
        response = c.post('/organization/%d/user/add/' % org.id, {'user':0})
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid post
        data = {'user':user.id}
        response = c.post('/organization/%d/user/add/' % org.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/user_row.html', response.template.name)
        self.assert_(org.users.filter(user=user).exists())
        
        # same user again
        response = c.post('/organization/%d/user/add/' % org.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals(org.users.filter(user=user).count(), 1)
    
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
        org = self.test_save()
        c = Client()
        org.users.add(user.get_profile())
        
        # invalid permissions
        response = c.get('/organization/%d/user/add/' % org.id)
        self.assertEqual(403, response.status_code)
        response = c.post('/organization/%d/user/add/' % org.id)
        self.assertEqual(403, response.status_code)
        
        # authorize and login
        self.assert_(c.login(username=user.username, password='secret'))
        grant(user, 'admin', org)
        
        # invalid method
        response = c.get('/organization/%d/user/remove/' % org.id)
        self.assertEqual(405, response.status_code)
        
        # valid request (perm)
        data = {'user':user.id}
        response = c.post('/organization/%d/user/remove/' % org.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(org.users.filter(user=user).exists())
        
        # valid request (superuser)
        revoke(user, 'admin', org)
        user.is_superuser = True
        user.save()
        org.users.add(user.get_profile())
        response = c.post('/organization/%d/user/remove/' % org.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(org.users.filter(user=user).exists())
        
        # remove user again
        response = c.post('/organization/%d/user/remove/' % org.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(org.users.filter(user=user).exists())
        self.assertNotEqual('1', response.content)
        
        # remove invalid user
        response = c.post('/organization/%d/user/remove/' % org.id, {'user':0})
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
        org = self.test_save()
        org.users.add(user.get_profile())
        
        register('Perm1', Organization)
        register('Perm2', Organization)
        
        c = Client()
        
        # unauthorized
        response = c.get('/organization/%d/user/%s/' % (org.id, 0))
        self.assertEqual(403, response.status_code)
        response = c.post('/organization/%d/user/%s/' % (org.id, 0))
        self.assertEqual(403, response.status_code)
        
        # authorized post (perm granted)
        grant(user, 'admin', org)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get('/organization/%d/user/%s/' % (org.id, user.id))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/permissions.html', response.template.name)
        
        # authorized post (superuser)
        revoke(user, 'admin', org)
        user.is_superuser = True
        user.save()
        
        response = c.get('/organization/%d/user/%s/' % (org.id, user.id))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/permissions.html', response.template.name)
        
        # invalid user
        response = c.post('/organization/%d/user/%s/' % (org.id, 0))
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # invalid permission
        data = {'permissions':['DoesNotExist']}
        response = c.post('/organization/%d/user/%s/' % (org.id, user.id), data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid post
        data = {'permissions':['Perm1','Perm2']}
        response = c.post('/organization/%d/user/%s/' % (org.id, user.id), data)
        self.assertEqual(200, response.status_code)
        
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertEqual('organizations/user_row.html', response.template.name)
        self.assert_(user.has_perm('Perm1', org))
        self.assert_(user.has_perm('Perm2', org))
        self.assertEqual(['Perm1','Perm2'], get_user_perms(user, org))