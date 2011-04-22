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

__all__ = ('TestUsersViews',)

class TestUsersViews(TestCase):
    """
    Tests for checking the update/delete/change of password of users
      that a superuser has access to.
    """
    def setUp(self):
        superuser = User(id=1, username='sudo', is_superuser=True)
        superuser.set_password('sudome')
        superuser.save()
        
        user = User(id=2, username='test')
        user.set_password('password')
        user.save()
        
        test_user = User(id=4, username='tester')
        test_user.set_password('testpassword')
        test_user.save()
        
        url_list = '/users'
        url_create = '/users/add'
        url_edit = '/user/%s/edit'
        url_password = '/user/%s/password/'
        
        g = globals()
        g['superuser'] = superuser
        g['user'] = user
        g['test_user'] = test_user
        g['c'] = Client()
        g['url_list'] = url_list
        g['url_create'] = url_create
        g['url_edit'] = url_edit
        g['url_password'] = url_password
    
    def tearDown(self):
        User.objects.all().delete()
    
    def test_view_list(self):
        """
        Test users list view
        """
        url = url_list
        
        # GET - Anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
    
        # GET - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        c.logout()
        
        # GET - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/list.html')
        self.assertTemplateUsed(response, 'users/table.html')
        c.logout()
        
    def test_view_create(self):
        """
        Test users creation view
        """
        url = url_create
        
        data = {'username':'bob',
                'password1':'newpassword',
                'password2':'newpassword'}
        
        # GET - Anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
    
        # GET - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        c.logout()
        
        # GET - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/edit.html')
        c.logout()
        
        # POST - Anonymous user
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertFalse(User.objects.filter(username=data['username']).exists())
        
        # POST - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertFalse(User.objects.filter(username=data['username']).exists())
        c.logout()
        
        # POST - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/list.html')
        self.assertTemplateUsed(response, 'users/table.html')
        self.assertTrue(User.objects.filter(username=data['username']).exists())
        c.logout()
    
    def test_view_edit(self):
        """
        Test users edit view/form
        """
        url = url_edit % test_user.id
        
        data = {
            'username':test_user.username,
            'email':'test@example.org',
            'new_password1':'',
            'new_password2':''
        }
        
        # GET - Anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
    
        # GET - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        c.logout()
        
        # GET - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        #self.assertContains(response, test_user.password)
        self.assertContains(response, test_user.username)
        self.assertTemplateUsed(response, 'users/edit.html')
        c.logout()
        
        # POST - Anonymous user
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertEqual(usercheck.first_name, '')
        
        # POST - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)
        usercheck = User.objects.get(id=test_user.id)
        self.assertEqual(usercheck.first_name, '')
        c.logout()
        
        # POST - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/list.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertEqual(usercheck.email, 'test@example.org')
        self.assertTrue(usercheck.check_password('testpassword'))
        
        data['new_password1'] = 'ahahaha'
        data['new_password2'] = ''
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/edit.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))

        data['new_password1'] = ''
        data['new_password2'] = 'ahahahaha'
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/edit.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))
        
        data['new_password1'] = 'oeudoeuid'
        data['new_password2'] = 'uidhp'
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/edit.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))

        data['new_password1'] = 'passwordshouldchange'
        data['new_password2'] = 'passwordshouldchange'
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/list.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertTrue(usercheck.check_password('passwordshouldchange'))

        c.logout()
    
    def test_view_delete(self):
        """
        Test deleting users using user_edit view
        """
        url = url_edit
        
        new_user = User(id=3, username='foobar')
        new_user.save()
        
        # DELETE - Anonymous User trying to delete
        response = c.delete(url % new_user.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(User.objects.filter(id=new_user.id).exists())
        
        # DELETE - User trying to delete test user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.delete(url % new_user.id)
        self.assertEqual(403, response.status_code)
        self.assertTrue(User.objects.filter(id=new_user.id).exists())
        c.logout()
        
        # DELETE - Superuser deleting test user
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.delete(url % new_user.id)
        self.assertEqual(200, response.status_code)
        self.assertFalse(User.objects.filter(id=new_user.id).exists())
        c.logout()
        
    def test_view_password(self):
        """
        Test changing a users password with the user_password view
        """
        url = url_password % -32
        
        # GET - Anonymous user, invalid user_id passed
        response = c.get(url, follow=True)
        self.assertEqual(404, response.status_code)
        
        url = url_password % test_user.id
        
        new_pass = 'asdfasdf'
        data = {'new_password1':new_pass,
                'new_password2':new_pass}
        
        # GET - Anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
    
        # GET - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.get(url, follow=True)
        self.assertEqual(403, response.status_code)
        c.logout()
        
        # GET - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/password.html')
        c.logout()
        
        # POST - Anonymous user
        response = c.post(url, data, follow=True)
        self.assertTrue(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(test_user.check_password('testpassword'))
        
        # POST - Normal user
        self.assertTrue(c.login(username=user.username, password='password'))
        response = c.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertTrue(test_user.check_password('testpassword'))
        c.logout()
        
        # POST - Superuser
        self.assertTrue(c.login(username=superuser.username, password='sudome'))
        self.assertTrue(test_user.check_password('testpassword'))
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'users/list.html')
        usercheck = User.objects.get(id=test_user.id)
        self.assertTrue(usercheck.check_password(new_pass))
        c.logout()
        
