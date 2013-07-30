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

from django.test import TestCase

from utils.proxy.constants import NODE

from virtualmachines.models import VirtualMachine
from clusters.models import Cluster
from nodes.models import Node


__all__ = ['TestNodeModel']


class NodeTestCaseMixin(object):

    def create_node(self, cluster=None, hostname='node1.example.bak'):
        if cluster is None:
            cluster = Cluster.objects.create(hostname='test.example.bak',
                                             slug='OSL_TEST')
        node = Node.objects.create(cluster=cluster, hostname=hostname)
        return node, cluster


class TestNodeModel(TestCase, NodeTestCaseMixin):

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
        node_hostname = 'node.test.org'
        cluster = Cluster.objects.create(hostname='test.example.bak',
                                         slug='OSL_TEST')

        # Cluster
        node = Node.objects.create(cluster=cluster, hostname=node_hostname)
        self.assertTrue(node.id)
        self.assertEqual('node.test.org', node.hostname)
        self.assertFalse(node.error)
        node.delete()

        cluster.delete()

    def test_save(self):
        """
        Test saving a VirtualMachine

        Verify:
            * Node can be saved
            * Node can be loaded
            * Hash is copied from cluster
        """
        node, cluster = self.create_node()
        self.assertTrue(node.id)
        self.assertFalse(node.error)
        self.assertEqual(node.cluster_hash, cluster.hash)

        node = Node.objects.get(id=node.id)
        self.assertTrue(node.info)
        self.assertFalse(node.error)

        node.delete()
        cluster.delete()

    def test_hash_update(self):
        """
        When cluster is saved hash for its VirtualMachines should be updated
        """
        node0, cluster = self.create_node()
        node1, cluster = self.create_node(cluster, 'test2.example.bak')

        self.assertEqual(node0.cluster_hash, cluster.hash)
        self.assertEqual(node1.cluster_hash, cluster.hash)

        # change cluster's hash
        cluster.hostname = 'SomethingDifferent'
        cluster.save()
        node0 = Node.objects.get(pk=node0.id)
        node1 = Node.objects.get(pk=node1.id)
        self.assertEqual(node0.cluster_hash, cluster.hash,
                         'VirtualMachine does not have updated cache')
        self.assertEqual(node1.cluster_hash, cluster.hash,
                         'VirtualMachine does not have updated cache')

        node0.delete()
        node1.delete()
        cluster.delete()

    def test_parse_info(self):
        """
        Test parsing values from cached info

        Verifies:
            * mtime and ctime are parsed
            * ram, virtual_cpus, and disksize are parsed
        """
        node, cluster = self.create_node()
        node.info = NODE

        self.assertEqual(node.ctime,
                         datetime.fromtimestamp(1285799513.4741000))
        self.assertEqual(node.mtime,
                         datetime.fromtimestamp(1285883187.8692000))
        self.assertFalse(node.offline)
        self.assertEqual(3, node.cpus)

        node.delete()
        cluster.delete()

    def test_ram(self):
        """
        Tests the Node.ram property
        """
        node, c = self.create_node()
        node2, c = self.create_node(cluster=c, hostname='two')
        node.refresh()
        node2.refresh()

        foo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='foo', ram=123,
                                            status='running')
        bar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='bar', ram=456,
                                            status='running')
        xoo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xoo', ram=789,
                                            status='admin_down')
        xar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='xar', ram=234,
                                            status='stopped')
        boo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='boo', status='running')
        gar = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='gar', ram=888,
                                            status='running')
        yoo = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='yoo', ram=999,
                                            status='admin_down')

        ram = node.ram
        self.assertEqual(9999, ram['total'])
        self.assertEqual(9420, ram['free'])
        self.assertEqual(8888, ram['used'])
        self.assertEqual(579, ram['allocated'])

        foo.delete()
        bar.delete()
        xoo.delete()
        xar.delete()
        boo.delete()
        gar.delete()
        yoo.delete()

        node.delete()
        node2.delete()
        c.delete()

    def test_disk(self):
        """
        Tests the Node.ram property
        """
        node, c = self.create_node()
        node2, c = self.create_node(cluster=c, hostname='two')
        node.refresh()
        node2.refresh()

        foo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='foo', disk_size=123,
                                            status='running')
        bar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='bar', disk_size=456,
                                            status='running')
        xoo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xoo', disk_size=789,
                                            status='admin_down')
        xar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='xar', disk_size=234,
                                            status='stopped')
        boo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='boo', status='running')
        gar = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='gar', disk_size=888,
                                            status='running')
        yoo = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='yoo', disk_size=999,
                                            status='admin_down')

        disk = node.disk
        self.assertEqual(6666, disk['total'])
        self.assertEqual(5064, disk['free'])
        self.assertEqual(4444, disk['used'])
        self.assertEqual(1602, disk['allocated'])

        foo.delete()
        bar.delete()
        xoo.delete()
        xar.delete()
        boo.delete()
        gar.delete()
        yoo.delete()

        node.delete()
        node2.delete()
        c.delete()

    def test_allocated_cpus(self):
        """
        tests Node.allocated_cpus property
        """
        node, c = self.create_node()
        node2, c = self.create_node(cluster=c, hostname='two')
        node.refresh()
        node2.refresh()

        foo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='foo', virtual_cpus=123,
                                            status='running')
        foo2 = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                             hostname='foo2', virtual_cpus=7,
                                             status='running')
        bar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='bar', virtual_cpus=456,
                                            status='running')
        xoo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xoo', virtual_cpus=789,
                                            status='admin_down')
        xar = VirtualMachine.objects.create(cluster=c, secondary_node=node,
                                            hostname='xar', virtual_cpus=234,
                                            status='stopped')
        boo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='boo', status='running')
        gar = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='gar', virtual_cpus=888,
                                            status='running')
        yoo = VirtualMachine.objects.create(cluster=c, primary_node=node2,
                                            hostname='yoo', virtual_cpus=999,
                                            status='admin_down')

        self.assertEqual(130, node.allocated_cpus)

        foo.delete()
        foo2.delete()
        bar.delete()
        xoo.delete()
        xar.delete()
        boo.delete()
        gar.delete()
        yoo.delete()

        node.delete()
        node2.delete()
        c.delete()
