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
    Tests for checking the update/delete/change of password of users that a
    superuser has access to.
    """

    def setUp(self):
        self.superuser = User(username='sudo', is_superuser=True)
        self.superuser.set_password('sudome')
        self.superuser.save()

        self.user = User(username='test')
        self.user.set_password('password')
        self.user.save()

        self.test_user = User(username='tester')
        self.test_user.set_password('testpassword')
        self.test_user.save()

        self.url_list = '/users'
        self.url_create = '/user/add'
        self.url_edit = '/user/%s/edit'
        self.url_password = '/user/%s/password/'
        self.c = Client()

    def tearDown(self):
        self.superuser.delete()
        self.user.delete()
        self.test_user.delete()

    def test_view_list_anonymous(self):
        """
        Test users list view
        """

        response = self.c.get(self.url_list, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_list(self):
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.get(self.url_list)
        self.assertEqual(403, response.status_code)

    def test_view_list_superuser(self):
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.get(self.url_list)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/list.html')
        self.assertTemplateUsed(response, 'user/table.html')

    def test_view_create_get_anonymous(self):
        """
        Test users creation view
        """

        response = self.c.get(self.url_create, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_create_get(self):
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.get(self.url_create)
        self.assertEqual(403, response.status_code)

    def test_view_create_get_superuser(self):
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.get(self.url_create)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/edit.html')

    def test_view_create_post_anonymous(self):
        data = {
            'username': 'bob',
            'password1': 'newpassword',
            'password2': 'newpassword',
            'email': 'tester@test.com',
        }

        response = self.c.post(self.url_create, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_view_create_post(self):
        data = {
            'username': 'bob',
            'password1': 'newpassword',
            'password2': 'newpassword',
            'email': 'tester@test.com',
        }

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.post(self.url_create, data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_view_create_post_superuser(self):
        data = {
            'username': 'bob',
            'password1': 'newpassword',
            'password2': 'newpassword',
            'email': 'tester@test.com',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(self.url_create, data)
        test_user = User.objects.latest('id')
        self.assertRedirects(response, test_user.get_absolute_url())
        self.assertTrue(User.objects.filter(username=data['username']).exists())

    def test_view_edit_get_anonymous(self):
        """
        Test users edit view/form
        """
        url = self.url_edit % self.test_user.id

        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_edit_get(self):
        url = self.url_edit % self.test_user.id

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

    def test_view_edit_get_superuser(self):
        url = self.url_edit % self.test_user.id

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        # XXX why would this happen?
        #self.assertContains(response, self.test_user.password)
        self.assertContains(response, self.test_user.username)
        self.assertTemplateUsed(response, 'user/edit.html')

    def test_view_edit_post_anonymous(self):
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': '',
            'new_password2': '',
        }

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertEqual(usercheck.first_name, '')

    def test_view_edit_post(self):
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': '',
            'new_password2': '',
        }

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertEqual(usercheck.first_name, '')

    def test_view_edit_post_superuser(self):
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': '',
            'new_password2': '',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(url, data)
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertRedirects(response, usercheck.get_absolute_url())
        self.assertEqual(usercheck.email, 'test@example.org')
        self.assertTrue(usercheck.check_password('testpassword'))

    def test_view_edit_post_password_first_blank(self):
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': 'ahahaha',
            'new_password2': '',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/edit.html')
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))

    def test_view_edit_post_password_second_blank(self):
        """
        Test users edit view/form
        """
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': '',
            'new_password2': 'ahahahaha',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/edit.html')
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))

    def test_view_edit_post_password_mismatch(self):
        """
        Test users edit view/form
        """
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': 'oeudoeuid',
            'new_password2': 'uidhp',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/edit.html')
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertTrue(usercheck.check_password('testpassword'))

    def test_view_edit_post_password(self):
        url = self.url_edit % self.test_user.id

        data = {
            'username': self.test_user.username,
            'email': 'test@example.org',
            'new_password1': 'passwordshouldchange',
            'new_password2': 'passwordshouldchange',
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.post(url, data)
        self.assertRedirects(response, self.test_user.get_absolute_url())
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertTrue(usercheck.check_password('passwordshouldchange'))

    def test_view_delete_anonymous(self):
        """
        Test deleting users using user_edit view
        """

        new_user = User(id=3, username='foobar')
        new_user.save()

        url = self.url_edit % new_user.id

        response = self.c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(User.objects.filter(id=new_user.id).exists())

        new_user.delete()

    def test_view_delete_user(self):
        new_user = User(id=3, username='foobar')
        new_user.save()

        url = self.url_edit % new_user.id

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.delete(url)
        self.assertEqual(403, response.status_code)
        self.assertTrue(User.objects.filter(id=new_user.id).exists())

        new_user.delete()

    def test_view_delete_superuser(self):
        new_user = User(id=3, username='foobar')
        new_user.save()

        url = self.url_edit % new_user.id

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.delete(url)
        self.assertEqual(200, response.status_code)
        self.assertFalse(User.objects.filter(id=new_user.id).exists())

    def test_view_password_anonymous_invalid(self):
        """
        Test changing a users password with the user_password view
        """

        url = self.url_password % -32

        response = self.c.get(url, follow=True)
        self.assertEqual(404, response.status_code)

    def test_view_password_get_anonymous(self):
        url = self.url_password % self.test_user.id

        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_password_get(self):
        url = self.url_password % self.test_user.id

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.get(url, follow=True)
        self.assertEqual(403, response.status_code)

    def test_view_password_get_superuser(self):
        url = self.url_password % self.test_user.id

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/password.html')

    def test_view_password_post_anonymous(self):
        url = self.url_password % self.test_user.id
        data = {
            'new_password1': "asdfasdf",
            'new_password2': "asdfasdf",
        }

        response = self.c.post(url, data, follow=True)
        self.assertTrue(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(self.test_user.check_password('testpassword'))

    def test_view_password_post_user(self):
        url = self.url_password % self.test_user.id
        data = {
            'new_password1': "asdfasdf",
            'new_password2': "asdfasdf",
        }

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='password'))
        response = self.c.post(url, data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertTrue(self.test_user.check_password('testpassword'))

    def test_view_password_post_superuser(self):
        url = self.url_password % self.test_user.id
        data = {
            'new_password1': "asdfasdf",
            'new_password2': "asdfasdf",
        }

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='sudome'))
        self.assertTrue(self.test_user.check_password('testpassword'))
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'user/list.html')
        usercheck = User.objects.get(id=self.test_user.id)
        self.assertTrue(usercheck.check_password("asdfasdf"))
