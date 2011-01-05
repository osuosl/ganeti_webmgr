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


from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from object_permissions import *


from ganeti.tests.rapi_proxy import RapiProxy, INFO, NODES, NODES_BULK
from ganeti import models
Cluster = models.Cluster


__all__ = ('TestGeneralViews', )


class TestGeneralViews(TestCase):
    
    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.tearDown()

        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.grant("admin", cluster)
        user1.save()
        
        dict_ = globals()
        dict_['user'] = user
        dict_['user1'] = user1
        dict_['cluster'] = cluster
        dict_['c'] = Client()
    
    def tearDown(self):
        Cluster.objects.all().delete()
        User.objects.all().delete()

    def test_view_index(self):
        """
        Tests redirections at /
        """
        url = "/"

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # authorized user (not admin)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, "virtual_machine/list.html")
        
        # authorized user (admin)
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, "cluster/overview.html")
        
        # authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, "cluster/overview.html")
