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


from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from ganeti_web.models import SSHKey, validate_sshkey


__all__ = ('TestSSHKeys',)

class TestSSHKeys(TestCase):

    def setUp(self):
        # anonymous user
        self.anonymous = User(id=1, username='anonymous')
        self.anonymous.save()
        settings.ANONYMOUS_USER_ID = self.anonymous.id

        # user
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()

        # user1
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()

        # admin == superuser
        admin = User(id=4, username='tester2', is_superuser=True)
        admin.set_password("secret")
        admin.save()

        # key
        key = SSHKey(key="ssh-rsa test tester0@testing", user=user)
        key.save()

        self.user = user
        self.user1 = user1
        self.admin = admin
        self.key = key
        self.c = Client()


    def tearDown(self):
        self.anonymous.delete()
        self.user.delete()
        self.user1.delete()
        self.admin.delete()
        self.key.delete()


    def test_permissions(self):
        """
        Tests accessing to views

        Verifies:
            * anon user is being forced to log in
            * not owner is not permitted
            * owner and admin are allowed
        """
        urls = {
            "get_new": reverse("key-get"),
            "get_existing": reverse("key-get", args=[self.key.id]),
            "save_new": reverse("key-save"),
            "save_existing": reverse("key-save", args=[self.key.id]),
            "delete": reverse("key-delete", args=[self.key.id]),
        }

        # Note: in this test no "real" deletion is performed
        # due to the request method, which here is always "GET".
        # The deletion works only for "DELETE"

        # test anonymous access
        for i in urls.values():
            response = self.c.get(i, follow=True)
            self.assertEqual(200, response.status_code)
            self.assertTemplateUsed(response, "registration/login.html")

        # test unauthorized access (== not owner)
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assertTrue(self.c.login(username=self.user1.username,
                                         password="secret"))
            response = self.c.get(i)
            self.assertEqual(403, response.status_code)

        # test owner access
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assertTrue(self.c.login(username=self.user.username,
                                         password="secret"))
            response = self.c.get(i)
            self.assertEqual(200, response.status_code)

        # test admin access
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assertTrue(self.c.login(username=self.admin.username,
                                         password="secret"))
            response = self.c.get(i)
            self.assertEqual(200, response.status_code)


    def test_getting(self):
        """
        Tests key_get views

        Verifies:
            * appropriate object is being got
            * new object is being created
            * 404 thrown for non-existant objects
        """
        for u in [self.user, self.admin]:
            self.c.login(username=u.username, password="secret")

            # appropriate object is being got
            response = self.c.get(reverse("key-get", args=[self.key.id]))
            self.assertEqual(200, response.status_code)
            self.assertEquals("text/html; charset=utf-8", response["content-type"])
            self.assertTemplateUsed(response, "ganeti/ssh_keys/form.html")
            self.assertContains(response, self.key.key, count=1)

            # new object is being created
            response = self.c.get(reverse("key-get"))
            self.assertEqual(200, response.status_code)
            self.assertEquals("text/html; charset=utf-8", response["content-type"])
            self.assertTemplateUsed(response, "ganeti/ssh_keys/form.html")
            self.assertNotContains(response, self.key.key)

            # 404 for non-existing object
            response = self.c.get(reverse("key-get", args=[self.key.id+10]))
            self.assertEqual(404, response.status_code)

    def test_admin_create(self):
        """
        Test an admin opening an ssh create form for another user
        """
        self.c.login(username=self.admin.username, password="secret")
        response = self.c.get('/user/%s/key/' % self.user.pk)
        self.assertEqual(200, response.status_code)
        self.assertEquals("text/html; charset=utf-8", response["content-type"])
        self.assertTemplateUsed(response, "ganeti/ssh_keys/form.html")

    def test_saving(self):
        """
        Tests key_save views

        Verifies:
            * thrown 404 for non-existing objects
            * returned form errors for invalid key
            * returned appropriate HTML row after saving
        """
        for u in [self.user, self.admin]:
            self.c.login(username=u.username, password="secret")

            # 404 for non-existing row
            response = self.c.get(reverse("key-save", args=[self.key.id+10]))
            self.assertEqual(404, response.status_code)

            # form errors
            # note: for this tests cannot be used assertFormError assertion
            #  * invalid key (existing object)
            response = self.c.post(reverse("key-save", args=[self.key.id]),
                                   {"key":"key"})
            self.assertEquals("application/json", response["content-type"])
            self.assertContains(response, validate_sshkey.message, count=1)
            #  * invalid key (new object)
            response = self.c.post(reverse("key-save"), {"key":"key"})
            self.assertEquals("application/json", response["content-type"])
            self.assertContains(response, validate_sshkey.message, count=1)
            #  * missing fields
            response = self.c.post(reverse("key-save", args=[self.key.id]))
            self.assertEquals("application/json", response["content-type"])
            self.assertNotContains(response, validate_sshkey.message)
            #  * missing fields
            response = self.c.post(reverse("key-save"))
            self.assertEquals("application/json", response["content-type"])
            self.assertNotContains(response, validate_sshkey.message)

            # successful creation of new object
            response = self.c.post(reverse("key-save"),
                                   {"key": "ssh-rsa t t@t",
                                    'user': self.user.pk})
            self.assertEqual(200, response.status_code)
            self.assertTemplateUsed(response, "ganeti/ssh_keys/row.html")
            self.assertContains(response, "t@t", count=1)

    def test_deletion(self):
        """
        Tests key_delete view

        Verifies:
            * thrown 404 for non-existing objects
            * successfully deleted objects
        """
        for u in [self.user, self.admin]:
            key1 = SSHKey(key="ssh-rsa test tester0@testing", user=u)
            key1.save()
            key_id = key1.id

            self.c.login(username=u.username, password="secret")

            # 404 for non-existing objects
            response = self.c.get(reverse("key-delete", args=[key_id+10]))
            self.assertEqual(404, response.status_code)

            # successful deletion
            response = self.c.delete(reverse("key-delete", args=[key_id]))
            self.assertEqual(200, response.status_code)
            self.assertEquals("application/json", response['content-type'])
            self.assertContains(response, "1", count=1)
            self.assertEqual(0, len(SSHKey.objects.filter(id=key_id)))
