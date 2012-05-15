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
from ganeti_web.models import Node

from ganeti_web.util.proxy import RapiProxy
from ganeti_web.util.proxy.constants import NODES
from ganeti_web import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Organization = models.Organization
Profile = models.Profile

__all__ = ['NodeMissingDBTests', 'NodeMissingTests']


class NodeImportBase(TestCase):
    url = ''
    c = None
    cluster0 = None
    cluster1 = None

    def setUp(self):
        self.tearDown()
        
        models.client.GanetiRapiClient = RapiProxy

        self.unauthorized = User(id=2, username='tester0')
        self.authorized = User(id=3, username='tester1')
        self.superuser = User(id=4, username='tester2', is_superuser=True)

        self.unauthorized.set_password('secret')
        self.authorized.set_password('secret')
        self.superuser.set_password('secret')
        
        self.unauthorized.save()
        self.authorized.save()
        self.superuser.save()

        self.cluster0 = Cluster.objects.create(hostname='test0', slug='OSL_TEST0')
        self.cluster1 = Cluster.objects.create(hostname='test1', slug='OSL_TEST1')

        self.authorized.grant('admin', self.cluster0)

        self.cluster0.rapi.GetNodes.response = ['node0','node2']
        self.cluster1.rapi.GetNodes.response = ['node3','node5']

        self.vm = VirtualMachine.objects.createhostname='gimager.example.bak', cluster=self.cluster0)

        self.node0 = Node.objects.create(hostname='node0', cluster=self.cluster0)
        self.node1 = Node.objects.create(hostname='node1', cluster=self.cluster0)
        self.node3 = Node.objects.create(hostname='node3', cluster=self.cluster1)
        self.node4 = Node.objects.create(hostname='node4', cluster=self.cluster1)

        self.c = Client()

    def tearDown(self):
        # reset proxy object default values, could cause collisions in other tests
        if self.cluster0 is not None:
            self.cluster0.rapi.GetNodes.response = NODES
        if self.cluster1 is not None:
            self.cluster1.rapi.GetNodes.response = NODES

        if self.c is not None:
            self.c.logout()
        Node.objects.all().delete()
        Cluster.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()

    def test_anonymous(self):
        """ anonymous user """
        response = self.c.get(self.url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_unauthorized(self):
        """ unauthorized user """
        self.assertTrue(self.c.login(username=self.unauthorized.username, password='secret'))
        response = self.c.get(self.url)
        self.assertEqual(403, response.status_code)


class NodeMissingDBTests(NodeImportBase):

    url = '/import/node/missing_db/'

    def test_get_form(self):
        """ authorized get (cluster admin perm) """
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        response = self.c.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/import.html')
        self.assertEqual([('%s:node2'%self.cluster0.pk,'test0','node2')], response.context['nodes'])

    def test_get_form_superuser(self):
        """ authorized get (superuser) """
        self.assertTrue(self.c.login(username=self.superuser.username, password='secret'))
        response = self.c.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/import.html')
        self.assertEqual([('%s:node2'%self.cluster0.pk,'test0','node2'), ('%s:node5'%self.cluster1.pk,'test1','node5')], response.context['nodes'])

    def test_invalid_node(self):
        """ POST - invalid node """
        self.assertTrue(self.c.login(username=self.superuser.username, password='secret'))
        data = {'nodes':[-1]}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/import.html')
        self.assertTrue(response.context['form'].errors)

    def test_unauthorized_post(self):
        """ POST - user does not have perms for cluster """
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        data = {'nodes':[self.node3.hostname]}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/import.html')
        self.assertTrue(response.context['form'].errors)

    def test_successful_import(self):
        """ POST - success """
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        data = {'nodes':['%s:node2'%self.cluster0.pk]}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/import.html')
        self.assertFalse(response.context['form'].errors)
        self.assertTrue(Node.objects.filter(hostname='node2').exists())
        self.assertEqual([], response.context['nodes'])

        # check to see that vm nodes were updated
        vm = VirtualMachine.objects.filter(hostname='gimager.example.bak') \
            .values_list('primary_node__hostname')[0][0]
        self.assertEqual('node2', vm)


class NodeMissingTests(NodeImportBase):

    url = '/import/node/missing/'

    def test_get_form_authorized(self):
        # authorized get (cluster admin perm)
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        response = self.c.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/missing.html')
        self.assertEqual([('node1','test0','node1')], response.context['nodes'])

    def test_get_form_superuser(self):
        """ authorized get (superuser) """
        self.assertTrue(self.c.login(username=self.superuser.username, password='secret'))
        response = self.c.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/missing.html')
        self.assertEqual([('node1','test0','node1'), ('node4','test1','node4')], response.context['nodes'])

    def test_invalid_node(self):
        """ POST - invalid vm """
        self.assertTrue(self.c.login(username=self.superuser.username, password='secret'))
        data = {'nodes':[-1]}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/missing.html')
        self.assertTrue(response.context['form'].errors)

    def test_post_unauthorized(self):
        """ POST - user does not have perms for cluster """
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        data = {'nodes':[self.node3.hostname]}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/missing.html')
        self.assertTrue(response.context['form'].errors)

    def test_successful_deletion(self):
        """ POST - success """
        self.assertTrue(self.c.login(username=self.authorized.username, password='secret'))
        data = {'nodes':['node1']}
        response = self.c.post(self.url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/nodes/missing.html')
        self.assertFalse(response.context['form'].errors)
        self.assertFalse(Node.objects.filter(hostname='node1').exists())
        self.assertEqual([], response.context['nodes'])
