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
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin
from ganeti_web.tests.models.node import NodeTestCaseMixin

from ganeti_web.tests.rapi_proxy import RapiProxy, NODE
from ganeti_web import models
from ganeti_web.util.client import GanetiApiError

from ganeti_web.views import node as view_node

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
Node = models.Node


__all__ = ['TestNodeViews']

global user_admin, user_migrate, superuser
global cluster, node

def cluster_default_info_proxy(cluster):
    return {
        'iallocator':'foo'
    }

view_node.cluster_default_info = cluster_default_info_proxy


class TestNodeViews(TestCase, NodeTestCaseMixin, UserTestMixin, ViewTestMixin):

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy

        node, cluster = self.create_node()
        node2, cluster = self.create_node(cluster, 'node2.osuosl.bak')

        d = globals()
        d['cluster'] = cluster
        d['node'] = node

        self.create_standard_users(d)
        self.create_users(['user_migrate', 'user_admin'], d)

        user_migrate.grant('migrate', cluster)
        user_admin.grant('admin', cluster)

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()

    def test_detail(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/node/detail.html')

    def test_primary_vms(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/primary'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/virtual_machine/table.html')

    def test_secondary_vms(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/secondary'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/virtual_machine/table.html')

    def test_object_log(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/object_log'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users)

    def test_role(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/role'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/node/role.html')

        # test posts
        def test(user, response):
            data = json.loads(response.content)
            self.assertTrue('opstatus' in data)
        data = {'role':'master-candidate'}
        self.assert_200(url, args, users, method='post', data=data, mime='application/json', tests=test)

        #test form error
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [superuser], method='post', \
                mime='application/json', data={}, tests=test)

        #test ganeti error
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        node.rapi.SetNodeRole.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], method='post', mime='application/json', data=data, tests=test)
        node.rapi.SetNodeRole.error = None

    def test_migrate(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/migrate'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/node/migrate.html')

        #test posts
        def test(user, response):
            data = json.loads(response.content)
            self.assertTrue('opstatus' in data)
        data = {'mode':'live'}
        self.assert_200(url, args, users, method='post', data=data, mime='application/json', tests=test)

        #test form error
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [superuser], method='post', \
                mime='application/json', data={}, tests=test)

        #test ganeti error
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        node.rapi.MigrateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], method='post', mime='application/json', data=data, tests=test)
        node.rapi.MigrateNode.error = None

    def test_evacuate(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/evacuate'
        users = [superuser, user_migrate, user_admin]

        self.assert_standard_fails(url, args, method='post')
        self.assert_200(url, args, users, template='ganeti/node/evacuate.html')

        # Test iallocator
        data = {'iallocator':True, 'iallocator_hostname':'foo', 'node':''}
        def tests(user, response):
            data = json.loads(response.content)
            self.assertTrue('status' in data, data)
            self.assertEqual('1', data['id'], data)
        self.assert_200(url, args, users, method='post', data=data, \
            tests=tests, mime="application/json")

        # Test node selection
        data = {'iallocator':False, 'iallocator_hostname':'foo', 'node':'node2.osuosl.bak'}
        self.assert_200(url, args, users, method='post', data=data, \
            tests=tests, mime="application/json")

        # Test form errors
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('status' in data, data)

        errors = [
            {'iallocator':False, 'iallocator_hostname':'foo', 'node':''} # must choose iallocator or a node
        ]
        self.assert_view_values(url, args, data, errors, mime='application/json', tests=test)

        # Test GanetiError
        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        node.rapi.EvacuateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], data=data, method='post', mime='application/json', tests=test)
        node.rapi.EvacuateNode.error = None
