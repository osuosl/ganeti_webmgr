# Copyright (C) 2010 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client


from ganeti_web.models import Profile


global user
global c


__all__ = ('TestProfileModel', 'TestAccountViews',)


class TestProfileModel(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()
    
    def test_trivial(self):
        """ Tests that object can be created """
        Profile()
    
    def test_signal_listeners(self):
        """
        Test automatic creation and deletion of profile objects
        """
        user = User(username='tester')
        user.save()
        
        # profile created
        profile = user.get_profile()
        self.assert_(profile, 'profile was not created')
        
        # profile deleted
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile.id).exists())


class TestAccountViews(TestCase):
    
    def setUp(self):
        self.tearDown()

        user = User(username='tester', email='test@test.com')
        user.set_password('secret')
        user.save()
        
        client = Client()
        
        g = globals()
        g['user'] = user
        g['c'] = client
    
    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()
    
    def test_view_login(self):
        """
        Test logging in
        """
        url = '/accounts/login/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # no username
        data = {'password':'secret'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # no password
        data = {'username':'tester'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # bad username
        data = {'username':'invalid', 'password':'secret'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # bad password
        data = {'username':'tester', 'password':'incorrect'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # user with perms on no virtual machines
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # invalid method
        data = {'username':'tester', 'password':'secret'}
        response = c.get(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # success
        data = {'username':'tester', 'password':'secret'}
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/overview.html')
    
    def test_view_logout(self):
        """
        Test logging out
        """
        url = '/accounts/logout/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # successful logout
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_view_profile(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'
        user = globals()['user']
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # get form
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        
        # bad method (CSRF check)
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(user.check_password('secret'), 'Password should not have been changed')
        
        # bad old password
        data = {'email':'new@test.com', 'old_password':'incorrect','new_password':'foo', 'confirm_password':'foo'}
        response = c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(user.check_password('secret'), 'Password should not have been changed')
        
        # not confirmed
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'incorrect'}
        response = c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('test@test.com', user.email)
        self.assert_(user.check_password('secret'), 'Password should not have been changed')
        
        # change email
        response = c.post(url, {'email':'new@test.com'})
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('new@test.com', user.email)
        self.assert_(user.check_password('secret'), 'Password should not have been changed')
        
        # change password
        data = {'email':'new2@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=user.id)
        self.assertEqual('new2@test.com', user.email)
        self.assert_(user.check_password('foo'), 'Password was not been changed')
