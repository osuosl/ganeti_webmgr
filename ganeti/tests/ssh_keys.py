# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
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


from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from ganeti.models import SSHKey, validate_sshkey


__all__ = ('TestSSHKeys', )

class TestSSHKeys(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        # anonymous user
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
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
        
        dict_ = globals()
        dict_['user'] = user
        dict_['user1'] = user1
        dict_['admin'] = admin
        dict_['key'] = key
        dict_['c'] = Client()


    def tearDown(self):
        SSHKey.objects.all().delete()
        Group.objects.all().delete()
        User.objects.all().delete()


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
            "get_existing": reverse("key-get", args=[key.id]),
            "save_new": reverse("key-save"),
            "save_existing": reverse("key-save", args=[key.id]),
            "delete": reverse("key-delete", args=[key.id]),
        }

        # Note: in this test no "real" deletion is performed
        # due to the request method, which here is always "GET".
        # The deletion works only for "DELETE"

        # test anonymous access
        for i in urls.values():
            response = c.get(i, follow=True)
            self.assertEqual(200, response.status_code)
            self.assertTemplateUsed(response, "registration/login.html")

        # test unauthorized access (== not owner)
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assert_( c.login(username=user1.username, password="secret") )
            response = c.get(i)
            self.assertEqual(403, response.status_code)

        # test owner access
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assert_( c.login(username=user.username, password="secret") )
            response = c.get(i)
            self.assertEqual(200, response.status_code)

        # test admin access
        for i in [ urls["get_existing"], urls["save_existing"], urls["delete"] ]:
            self.assert_( c.login(username=admin.username, password="secret") )
            response = c.get(i)
            self.assertEqual(200, response.status_code)


    def test_getting(self):
        """
        Tests key_get views

        Verifies:
            * appropriate object is being got
            * new object is being created
            * 404 thrown for non-existant objects
        """
        for u in [user, admin]:
            c.login(username=u.username, password="secret")

            # appropriate object is being got
            response = c.get( reverse("key-get", args=[key.id]) )
            self.assertEqual( 200, response.status_code )
            self.assertEquals("text/html; charset=utf-8", response["content-type"])
            self.assertTemplateUsed(response, "ssh_keys/form.html")
            self.assertContains(response, key.key, count=1)

            # new object is being created
            response = c.get( reverse("key-get") )
            self.assertEqual( 200, response.status_code )
            self.assertEquals("text/html; charset=utf-8", response["content-type"])
            self.assertTemplateUsed(response, "ssh_keys/form.html")
            self.assertNotContains(response, key.key,)

            # 404 for non-existing object
            response = c.get( reverse("key-get", args=[key.id+10]) )
            self.assertEqual( 404, response.status_code )

    def test_saving(self):
        """
        Tests key_save views

        Verifies:
            * thrown 404 for non-existing objects
            * returned form errors for invalid key
            * returned appropriate HTML row after saving
        """
        for u in [user, admin]:
            c.login(username=u.username, password="secret")

            # 404 for non-existing row
            response = c.get( reverse("key-save", args=[key.id+10]) )
            self.assertEqual( 404, response.status_code )

            # form errors
            # note: for this tests cannot be used assertFormError assertion
            #  * invalid key (existing object)
            response = c.post( reverse("key-save", args=[key.id]), {"key":"key"} )
            self.assertEquals("application/json", response["content-type"])
            self.assertContains( response, validate_sshkey.message, count=1 )
            #  * invalid key (new object)
            response = c.post( reverse("key-save"), {"key":"key"} )
            self.assertEquals("application/json", response["content-type"])
            self.assertContains( response, validate_sshkey.message, count=1 )
            #  * missing fields
            response = c.post( reverse("key-save", args=[key.id]) )
            self.assertEquals( "application/json", response["content-type"] )
            self.assertNotContains( response, validate_sshkey.message )
            #  * missing fields
            response = c.post( reverse("key-save") )
            self.assertEquals( "application/json", response["content-type"] )
            self.assertNotContains( response, validate_sshkey.message )

            # successful creation of new object
            response = c.post( reverse("key-save"), {"key": "ssh-rsa t t@t"})
            self.assertEqual( 200, response.status_code )
            self.assertTemplateUsed( response, "ssh_keys/row.html" )
            self.assertContains( response, "t@t", count=1 )

    def test_deletion(self):
        """
        Tests key_delete view

        Verifies:
            * thrown 404 for non-existing objects
            * successfully deleted objects
        """
        for u in [user, admin]:
            key1 = SSHKey(key="ssh-rsa test tester0@testing", user=user)
            key1.save()
            key_id = key1.id

            c.login(username=u.username, password="secret")

            # 404 for non-existing objects
            response = c.get( reverse("key-delete", args=[key_id+10]) )
            self.assertEqual( 404, response.status_code )

            # successful deletion
            response = c.delete( reverse("key-delete", args=[key_id]) )
            self.assertEqual( 200, response.status_code )
            self.assertEquals("application/json", response['content-type'])
            self.assertContains(response, "1", count=1)
            self.assertEqual(0, len(SSHKey.objects.filter(id=key_id)) )
