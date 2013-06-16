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

from .models import NodeTestCaseMixin

from utils import client
from utils.proxy import RapiProxy
from ganeti_web.util.client import GanetiApiError

from clusters.models import Cluster
from virtualmachines.models import VirtualMachine
from nodes.models import Node


__all__ = ['TestNodeViews']


class TestNodeViews(TestCase, NodeTestCaseMixin, UserTestMixin, ViewTestMixin):

    def setUp(self):
        client.GanetiRapiClient = RapiProxy

        self.node, cluster = self.create_node()
        self.node2, self.cluster = self.create_node(cluster,
                                                    'node2.example.bak')

        context = {"cluster": self.cluster, "node": self.node}

        self.create_standard_users(context)
        self.create_users(['user_migrate', 'user_admin'], context)

        self.user_migrate.grant('migrate', cluster)
        self.user_admin.grant('admin', cluster)

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()

    def test_trivial(self):
        pass

    def test_detail(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args, authorized=False)
        self.assert_200(url, args, users, 'ganeti/node/detail.html')

    def test_primary_vms(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/primary'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/virtual_machine/list.html')

    def test_secondary_vms(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/secondary'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/virtual_machine/list.html')

    def test_object_log(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/object_log'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users)

    def test_role(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/role'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/node/role.html')

    def test_role_post(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/role'
        users = [self.superuser, self.user_migrate, self.user_admin]

        def test(user, response):
            data = json.loads(response.content)
            self.assertTrue('opstatus' in data)
        data = {'role': 'master-candidate'}
        self.assert_200(url, args, users, method='post', data=data,
                        mime='application/json', tests=test)

    def test_role_error_form(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/role'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [self.superuser], method='post',
                        mime='application/json', data={}, tests=test)

    def test_role_error_ganeti(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/role'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        data = {'role': 'master-candidate'}
        self.node.rapi.SetNodeRole.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [self.superuser], method='post',
                        mime='application/json', data=data, tests=test)
        self.node.rapi.SetNodeRole.error = None

    def test_migrate(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/migrate'
        users = [self.superuser, self.user_migrate, self.user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'ganeti/node/migrate.html')

    def test_migrate_post(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/migrate'
        users = [self.superuser, self.user_migrate, self.user_admin]

        def test(user, response):
            data = json.loads(response.content)
            self.assertTrue('opstatus' in data)
        data = {'mode': 'live'}
        self.assert_200(url, args, users, method='post', data=data,
                        mime='application/json', tests=test)

    def test_migrate_error_form(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/migrate'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [self.superuser], method='post',
                        mime='application/json', data={}, tests=test)

    def test_migrate_error_ganeti(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/migrate'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        data = {'mode': 'live'}
        self.node.rapi.MigrateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [self.superuser], method='post',
                        mime='application/json', data=data, tests=test)
        self.node.rapi.MigrateNode.error = None

    def test_evacuate(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/evacuate'
        users = [self.superuser, self.user_migrate, self.user_admin]

        self.assert_standard_fails(url, args, method='post')
        self.assert_200(url, args, users, template='ganeti/node/evacuate.html')

    def test_evacuate_iallocator(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/evacuate'
        users = [self.superuser, self.user_migrate, self.user_admin]

        data = {'iallocator': True, 'iallocator_hostname': 'foo', 'node': ''}

        def tests(user, response):
            data = json.loads(response.content)
            self.assertTrue('status' in data, data)
            self.assertEqual('1', data['id'], data)
        self.assert_200(url, args, users, method='post', data=data,
                        tests=tests, mime="application/json")

    def test_evacuate_select_node(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/evacuate'
        users = [self.superuser, self.user_migrate, self.user_admin]

        data = {'iallocator': False, 'iallocator_hostname': 'foo',
                'node': 'node2.example.bak'}

        def tests(user, response):
            data = json.loads(response.content)
            self.assertTrue('status' in data, data)
            self.assertEqual('1', data['id'], data)
        self.assert_200(url, args, users, method='post', data=data,
                        tests=tests, mime="application/json")

    def test_evacuate_error_form(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/evacuate'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('status' in data, data)
        data = {'iallocator': False, 'iallocator_hostname': 'foo',
                'node': 'node2.example.bak'}

        errors = [
            # must choose iallocator or a node
            # XXX what does that even mean?
            {'iallocator': False, 'iallocator_hostname': 'foo', 'node': ''}
        ]
        self.assert_view_values(url, args, data, errors,
                                mime='application/json', tests=test)

    def test_evacuate_error_ganeti(self):
        args = (self.cluster.slug, self.node.hostname)
        url = '/cluster/%s/node/%s/evacuate'

        def test(user, response):
            data = json.loads(response.content)
            self.assertFalse('opstatus' in data)
        data = {'iallocator': False, 'iallocator_hostname': 'foo',
                'node': 'node2.example.bak'}
        self.node.rapi.EvacuateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [self.superuser], data=data, method='post',
                        mime='application/json', tests=test)
        self.node.rapi.EvacuateNode.error = None
