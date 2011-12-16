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


__all__ = ('TestProfileModel', 'TestAccountViews',)


class TestProfileModel(TestCase):

    def test_signal_listeners(self):
        """
        Test automatic creation and deletion of profile objects.
        """

        user = User(username='tester')
        user.save()

        # profile created
        profile = user.get_profile()
        self.assertTrue(profile, 'profile was not created')

        # profile deleted
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile.id).exists())


class TestAccountViews(TestCase):

    def setUp(self):
        user = User(username='tester', email='test@test.com')
        user.set_password('secret')
        user.save()

        self.c = Client()
        self.user = user

    def tearDown(self):
        self.user.delete()

    def test_view_login_anonymous(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_no_username(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # no username
        data = {'password':'secret'}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_no_password(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # no password
        data = {'username':'tester'}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_invalid_username(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # bad username
        data = {'username':'invalid', 'password':'secret'}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_invalid_password(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # bad password
        data = {'username':'tester', 'password':'incorrect'}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_no_perms(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # user with perms on no virtual machines
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_invalid_method(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # invalid method
        data = {'username':'tester', 'password':'secret'}
        response = self.c.get(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_login_success(self):
        """
        Test logging in
        """
        url = '/accounts/login/'

        # success
        data = {'username':'tester', 'password':'secret'}
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/overview.html')

    def test_view_logout_anonymous(self):
        """
        Test logging out
        """
        url = '/accounts/logout/'

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_logout_success(self):
        """
        Test logging out
        """
        url = '/accounts/logout/'

        # successful logout
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_profile_anonymous(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_profile_form(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')

    def test_view_profile_invalid_method(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.c.get(url)

        # bad method (CSRF check)
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = self.c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=self.user.id)
        self.assertEqual('test@test.com', user.email)
        self.assertTrue(user.check_password('secret'), 'Password should not have been changed')

    def test_view_profile_invalid_old_password(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.c.get(url)

        # bad old password
        data = {'email':'new@test.com', 'old_password':'incorrect','new_password':'foo', 'confirm_password':'foo'}
        response = self.c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=self.user.id)
        self.assertEqual('test@test.com', user.email)
        self.assertTrue(user.check_password('secret'), 'Password should not have been changed')

    def test_view_profile_unconfirmed(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.c.get(url)

        # not confirmed
        data = {'email':'new@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'incorrect'}
        response = self.c.get(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=self.user.id)
        self.assertEqual('test@test.com', user.email)
        self.assertTrue(user.check_password('secret'), 'Password should not have been changed')

    def test_view_profile_change_email(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.c.get(url)

        # change email
        response = self.c.post(url, {'email':'new@test.com'})
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=self.user.id)
        self.assertEqual('new@test.com', user.email)
        self.assertTrue(user.check_password('secret'), 'Password should not have been changed')

    def test_view_profile_change_password(self):
        """
        Tests updating a user profile
        """
        url = '/accounts/profile/'

        # get form
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.c.get(url)

        # change password
        data = {'email':'new2@test.com', 'old_password':'secret','new_password':'foo', 'confirm_password':'foo'}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/users/profile.html')
        user = User.objects.get(id=self.user.id)
        self.assertEqual('new2@test.com', user.email)
        self.assertTrue(user.check_password('foo'), 'Password was not been changed')
