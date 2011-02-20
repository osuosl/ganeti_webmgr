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

from datetime import datetime
import json

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from util import client
from ganeti.tests.rapi_proxy import RapiProxy, NODE
from ganeti import models
from util.client import GanetiApiError

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
Node = models.Node


__all__ = (
    'TestNodeModel',
    'TestNodeViews',
)


class NodeTestCaseMixin():
    def create_node(self, cluster=None, hostname='node1.osuosl.bak'):
        cluster = cluster if cluster else Cluster.objects \
            .create(hostname='test.osuosl.bak', slug='OSL_TEST')
        node = Node.objects.create(cluster=cluster, hostname=hostname)
        return node, cluster


class TestNodeModel(TestCase, NodeTestCaseMixin):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()
    
    def test_trivial(self):
        """
        Test instantiating a VirtualMachine
        """
        Node()
    
    def test_non_trivial(self):
        """
        Test instantiating a VirtualMachine with extra parameters
        """
        # Define cluster for use
        node_hostname='node.test.org'
        cluster = Cluster.objects.create(hostname='test.osuosl.bak', slug='OSL_TEST')
        
        # Cluster
        node = Node.objects.create(cluster=cluster, hostname=node_hostname)
        self.assertTrue(node.id)
        self.assertEqual('node.test.org', node.hostname)
        self.assertFalse(node.error)
        node.delete()
        
        # Multiple
        node = Node.objects.create(cluster=cluster, hostname=node_hostname)
        self.assertTrue(node.id)
        self.assertEqual('node.test.org', node.hostname)
        self.assertFalse(node.error)
        
        # test unique constraints
        node = Node(cluster=cluster, hostname=node_hostname)
        self.assertRaises(IntegrityError, node.save)
        
        # Remove cluster
        Cluster.objects.all().delete();
    
    def test_save(self):
        """
        Test saving a VirtualMachine
        
        Verify:
            * Node can be saved
            * Node can be loaded
            * Hash is copied from cluster
        """
        node, cluster = self.create_node()
        self.assert_(node.id)
        self.assertFalse(node.error)
        self.assertEqual(node.cluster_hash, cluster.hash)
        
        node = Node.objects.get(id=node.id)
        self.assert_(node.info)
        self.assertFalse(node.error)
    
    def test_hash_update(self):
        """
        When cluster is saved hash for its VirtualMachines should be updated
        """
        node0, cluster = self.create_node()
        node1, cluster = self.create_node(cluster, 'test2.osuosl.bak')
        
        self.assertEqual(node0.cluster_hash, cluster.hash)
        self.assertEqual(node1.cluster_hash, cluster.hash)
        
        # change cluster's hash
        cluster.hostname = 'SomethingDifferent'        
        cluster.save()
        node0 = Node.objects.get(pk=node0.id)
        node1 = Node.objects.get(pk=node1.id)
        self.assertEqual(node0.cluster_hash, cluster.hash, 'VirtualMachine does not have updated cache')
        self.assertEqual(node1.cluster_hash, cluster.hash, 'VirtualMachine does not have updated cache')
    
    def test_parse_info(self):
        """
        Test parsing values from cached info
        
        Verifies:
            * mtime and ctime are parsed
            * ram, virtual_cpus, and disksize are parsed
        """
        node, cluster = self.create_node()
        node.info = NODE
        
        self.assertEqual(node.ctime, datetime.fromtimestamp(1285799513.4741000))
        self.assertEqual(node.mtime, datetime.fromtimestamp(1285883187.8692000))
        self.assertFalse(node.offline)
    
    def test_ram(self):
        """
        Tests the Node.ram property
        """
        node, c = self.create_node()
        node2, c = self.create_node(cluster=c, hostname='two')
        node.refresh()
        node2.refresh()
        
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='foo', ram=123, status='running')
        VirtualMachine.objects.create(cluster=c, secondary_node=node, hostname='bar', ram=456, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xoo', ram=789, status='admin_down')
        VirtualMachine.objects.create(cluster=c, secondary_node=node, hostname='xar', ram=234, status='stopped')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='boo', status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node2, hostname='gar', ram=888, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node2, hostname='yoo', ram=999, status='admin_down')
        
        ram = node.ram
        self.assertEqual(9999, ram['total'])
        self.assertEqual(9420, ram['free'])
    
    def test_disk(self):
        """
        Tests the Node.ram property
        """
        node, c = self.create_node()
        node2, c = self.create_node(cluster=c, hostname='two')
        node.refresh()
        node2.refresh()

        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='foo', disk_size=123, status='running')
        VirtualMachine.objects.create(cluster=c, secondary_node=node, hostname='bar', disk_size=456, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xoo', disk_size=789, status='admin_down')
        VirtualMachine.objects.create(cluster=c, secondary_node=node, hostname='xar', disk_size=234, status='stopped')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='boo', status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node2, hostname='gar', disk_size=888, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node2, hostname='yoo', disk_size=999, status='admin_down')
        
        disk = node.disk
        self.assertEqual(6666, disk['total'])
        self.assertEqual(5064, disk['free'])


class TestNodeViews(TestCase, NodeTestCaseMixin, UserTestMixin, ViewTestMixin):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
        
        node, cluster = self.create_node()
        
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
        self.assert_200(url, args, users, 'node/detail.html')
    
    def test_primary_vms(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/primary'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'virtual_machine/table.html')
    
    def test_secondary_vms(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/secondary'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'virtual_machine/table.html')

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
        self.assert_200(url, args, users, 'node/role.html')
        
        # test posts
        def test(user, response):
            data = json.loads(response.content);
            self.assertTrue('opstatus' in data)
        data = {'role':'master'}
        self.assert_200(url, args, users, method='post', data=data, mime='application/json', tests=test)
        
        #test form error
        def test(user, response):
            data = json.loads(response.content);
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [superuser], method='post', \
                mime='application/json', data={}, tests=test)

        #test ganeti error
        def test(user, response):
            data = json.loads(response.content);
            self.assertFalse('opstatus' in data)
        node.rapi.SetNodeRole.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], method='post', mime='application/json', data=data, tests=test)
        node.rapi.SetNodeRole.error = None

    def test_migrate(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/migrate'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, 'node/migrate.html')
        
        #test posts
        def test(user, response):
            data = json.loads(response.content);
            self.assertTrue('opstatus' in data)
        data = {'live':True}
        self.assert_200(url, args, users, method='post', data=data, mime='application/json', tests=test)
        
        #test form error
        def test(user, response):
            data = json.loads(response.content);
            self.assertFalse('opstatus' in data)
        self.assert_200(url, args, [superuser], method='post', \
                mime='application/json', data={}, tests=test)

        #test ganeti error
        def test(user, response):
            data = json.loads(response.content);
            self.assertFalse('opstatus' in data)
        node.rapi.MigrateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], method='post', mime='application/json', data=data, tests=test)
        node.rapi.MigrateNode.error = None
    
    
    def test_evacuate(self):
        args = (cluster.slug, node.hostname)
        url = '/cluster/%s/node/%s/evacuate'
        users = [superuser, user_migrate, user_admin]
        self.assert_standard_fails(url, args, method='post')
        self.assert_200(url, args, users, method='post', mime="application/json")

        # Test GanetiError
        def test(user, response):
            data = json.loads(response.content);
            self.assertFalse('opstatus' in data)
        node.rapi.EvacuateNode.error = GanetiApiError("Testing Error")
        self.assert_200(url, args, [superuser], method='post', mime='application/json', tests=test)
        node.rapi.EvacuateNode.error = None