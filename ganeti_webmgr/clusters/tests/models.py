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

from django.contrib.auth.models import User
from django.test import TestCase

from ganeti_webmgr.utils.proxy.constants import INFO, JOB_RUNNING, JOB

from ganeti_webmgr.virtualmachines.models import VirtualMachine
from ganeti_webmgr.clusters.models import Cluster
from ganeti_webmgr.jobs.models import Job
from ganeti_webmgr.nodes.models import Node
from ganeti_webmgr.utils.models import Quota


__all__ = ['TestClusterModel']


class TestClusterModel(TestCase):

    def test_instantiation(self):
        """
        Test creating a Cluster Object
        """
        Cluster()

    def test_save(self):
        """
        test saving a cluster object

        Verifies:
            * object is saved and queryable
            * hash is updated
        """

        # XXX any reason why these are in a single test?
        cluster = Cluster()
        cluster.save()
        self.assertTrue(cluster.hash)
        cluster.delete()

        cluster = Cluster(hostname='foo.fake.hostname', slug='different')
        cluster.save()
        self.assertTrue(cluster.hash)
        cluster.delete()

    def test_parse_info(self):
        """
        Test parsing values from cached info

        Verifies:
            * mtime and ctime are parsed
            * ram, virtual_cpus, and disksize are parsed
        """
        cluster = Cluster(hostname='foo.fake.hostname')
        cluster.save()
        cluster.info = INFO

        self.assertEqual(cluster.ctime,
                         datetime.fromtimestamp(1270685309.818239))
        self.assertEqual(cluster.mtime,
                         datetime.fromtimestamp(1283552454.2998919))

        cluster.delete()

    def test_get_quota(self):
        """
        Tests cluster.get_quota() method

        Verifies:
            * if no user is passed, return default quota values
            * if user has quota, return values from Quota
            * if user doesn't have quota, return default cluster values
        """
        default_quota = {'default': 1, 'ram': 1,
                         'virtual_cpus': None, 'disk': 3}
        user_quota = {'default': 0, 'ram': 4, 'virtual_cpus': 5, 'disk': None}

        cluster = Cluster(hostname='foo.fake.hostname')
        cluster.__dict__.update(default_quota)
        cluster.save()
        user = User(username='tester')
        user.save()

        # default quota
        self.assertEqual(default_quota, cluster.get_quota())

        # user without quota, defaults to default
        self.assertEqual(default_quota, cluster.get_quota(user.get_profile()))

        # user with custom quota
        quota = Quota(cluster=cluster, user=user.get_profile())
        quota.__dict__.update(user_quota)
        quota.save()
        self.assertEqual(user_quota, cluster.get_quota(user.get_profile()))

        quota.delete()
        cluster.delete()
        user.delete()

    def test_set_quota(self):
        """
        Tests cluster.set_quota()

        Verifies:
            * passing values with no quota, creates a new quota object
            * passing values with an existing quota, updates it.
            * passing a None with an existing quota deletes it
            * passing a None with no quota, does nothing
        """
        default_quota = {'default': 1, 'ram': 1,
                         'virtual_cpus': None, 'disk': 3}
        user_quota = {'default': 0, 'ram': 4, 'virtual_cpus': 5, 'disk': None}
        user_quota2 = {'default': 0, 'ram': 7, 'virtual_cpus': 8, 'disk': 9}

        cluster = Cluster(hostname='foo.fake.hostname')
        cluster.__dict__.update(default_quota)
        cluster.save()
        user = User(username='tester')
        user.save()

        # create new quota
        cluster.set_quota(user.get_profile(), user_quota)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assertTrue(query.exists())
        self.assertEqual(user_quota, cluster.get_quota(user.get_profile()))

        # update quota with new values
        cluster.set_quota(user.get_profile(), user_quota2)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assertEqual(1, query.count())
        self.assertEqual(user_quota2, cluster.get_quota(user.get_profile()))

        # delete quota
        cluster.set_quota(user.get_profile(), None)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assertFalse(query.exists())
        self.assertEqual(default_quota, cluster.get_quota(user.get_profile()))

        cluster.delete()
        user.delete()

    def test_sync_virtual_machines(self):
        """
        Tests synchronizing cached virtuals machines (stored in db) with info
        the ganeti cluster is storing

        Verifies:
            * VMs no longer in ganeti are deleted
            * VMs missing from the database are added
        """
        cluster = Cluster(hostname='ganeti.example.test')
        cluster.save()
        vm_missing = 'gimager.example.bak'
        vm_current = VirtualMachine(cluster=cluster,
                                    hostname='gimager2.example.bak')
        vm_removed = VirtualMachine(cluster=cluster,
                                    hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()

        cluster.sync_virtual_machines()
        self.assertTrue(VirtualMachine.objects.get(cluster=cluster,
                                                   hostname=vm_missing),
                        'missing vm was not created')
        self.assertTrue(
            VirtualMachine.objects.get(
                cluster=cluster,
                hostname=vm_current.hostname),
            'previously existing vm was not created')
        self.assertTrue(
            VirtualMachine.objects.filter(
                cluster=cluster,
                hostname=vm_removed.hostname),
            "vm not in ganeti was not removed from db")

        cluster.sync_virtual_machines(True)
        self.assertFalse(
            VirtualMachine.objects.filter(
                cluster=cluster,
                hostname=vm_removed.hostname),
            'vm not present in ganeti was not removed from db')

        vm_removed.delete()
        vm_current.delete()
        cluster.delete()

    def test_sync_nodes(self):
        """
        Tests synchronizing cached Nodes (stored in db) with info
        the ganeti cluster is storing

        Verifies:
            * Node no longer in ganeti are deleted
            * Nodes missing from the database are added
        """
        cluster = Cluster.objects.create(hostname='ganeti.example.test')
        node_missing = 'gtest1.example.bak'
        node_current = Node.objects.create(cluster=cluster,
                                           hostname='gtest2.example.bak')
        node_removed = Node.objects.create(cluster=cluster,
                                           hostname='does.not.exist.org')

        cluster.sync_nodes()
        self.assertTrue(
            Node.objects.get(
                cluster=cluster,
                hostname=node_missing),
            'missing node was not created')
        self.assertTrue(
            Node.objects.get(
                cluster=cluster,
                hostname=node_current.hostname),
            'previously existing node was not created')
        self.assertTrue(
            Node.objects.filter(
                cluster=cluster,
                hostname=node_removed.hostname),
            'node not present in ganeti was not removed from db, '
            'even though remove flag was false')

        cluster.sync_nodes(True)
        self.assertFalse(
            Node.objects.filter(
                cluster=cluster,
                hostname=node_removed.hostname),
            'node not present in ganeti was not removed from db')

        node_current.delete()
        node_removed.delete()
        cluster.delete()

    def test_missing_in_database(self):
        """
        Tests missing_in_ganeti property
        """
        cluster = Cluster(hostname='ganeti.example.test')
        cluster.save()
        vm_current = VirtualMachine(cluster=cluster,
                                    hostname='gimager2.example.bak')
        vm_removed = VirtualMachine(cluster=cluster,
                                    hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()

        self.assertEqual([u'gimager.example.bak'], cluster.missing_in_db)

        vm_current.delete()
        vm_removed.delete()
        cluster.delete()

    def test_missing_in_ganeti(self):
        """
        Tests missing_in_ganeti property
        """
        cluster = Cluster(hostname='ganeti.example.test')
        cluster.save()
        vm_current = VirtualMachine(cluster=cluster,
                                    hostname='gimager2.example.bak')
        vm_removed = VirtualMachine(cluster=cluster,
                                    hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()

        self.assertEqual([u'does.not.exist.org'], cluster.missing_in_ganeti)

        vm_current.delete()
        vm_removed.delete()
        cluster.delete()

    def test_available_ram(self):
        """
        Tests that the available_ram property returns the correct values
        """
        c = Cluster.objects.create(hostname='ganeti.example.test')
        c2 = Cluster.objects.create(hostname='ganeti2.example.test',
                                    slug='argh')
        node = Node.objects.create(cluster=c, hostname='node.example.test')
        node1 = Node.objects.create(cluster=c2, hostname='node1.example.test')

        foo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='foo', ram=123,
                                            status='running')
        bar = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='bar', ram=456,
                                            status='running')
        xoo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xoo', ram=789,
                                            status='admin_down')
        xar = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xar', ram=234,
                                            status='stopped')
        boo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='boo', status='running')
        gar = VirtualMachine.objects.create(cluster=c2, primary_node=node1,
                                            hostname='gar', ram=888,
                                            status='running')
        yoo = VirtualMachine.objects.create(cluster=c2, primary_node=node1,
                                            hostname='yoo', ram=999,
                                            status='admin_down')

        # test with no nodes, should result in
        # zeros since nodes info isn't cached yet
        ram = c.available_ram
        self.assertEqual(0, ram['free'])
        self.assertEqual(0, ram['total'])
        self.assertEqual(0, ram['used'])
        self.assertEqual(579, ram['allocated'])

        # force refresh of nodes and rerun test for real values
        node.refresh()
        node1.refresh()
        ram = c.available_ram
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
        node1.delete()
        c.delete()
        c2.delete()

    def test_available_disk(self):
        """
        Tests that the available_disk property returns the correct values
        """
        c = Cluster.objects.create(hostname='ganeti.example.test')
        c2 = Cluster.objects.create(hostname='ganeti2.example.test',
                                    slug='argh')
        node = Node.objects.create(cluster=c, hostname='node.example.test')
        node1 = Node.objects.create(cluster=c2, hostname='node1.example.test')

        foo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='foo', disk_size=123,
                                            status='running')
        bar = VirtualMachine.objects.create(cluster=c,
                                            primary_node=node, hostname='bar',
                                            disk_size=456, status='running')
        xoo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xoo', disk_size=789,
                                            status='admin_down')
        xar = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='xar', disk_size=234,
                                            status='stopped')
        boo = VirtualMachine.objects.create(cluster=c, primary_node=node,
                                            hostname='boo', status='running')
        gar = VirtualMachine.objects.create(cluster=c2, primary_node=node1,
                                            hostname='gar', disk_size=888,
                                            status='running')
        yoo = VirtualMachine.objects.create(cluster=c2, primary_node=node1,
                                            hostname='yoo', disk_size=999,
                                            status='admin_down')

        # test with no nodes, should result in
        # zeros since nodes info isn't cached yet
        disk = c.available_disk
        self.assertEqual(0, disk['free'])
        self.assertEqual(0, disk['total'])
        self.assertEqual(0, disk['used'])
        self.assertEqual(1602, disk['allocated'])

        # force refresh of nodes and rerun test for real values
        node.refresh()
        node1.refresh()
        disk = c.available_disk
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
        node1.delete()
        c.delete()
        c2.delete()

    def test_redistribute_config(self):
        """
        Test Cluster.redistribute_config()

        Verifies:
            * job is created
            * cache is disabled while job is running
            * cache is reenabled when job is finished
        """
        cluster = Cluster.objects.create(hostname='ganeti.example.test')
        cluster.rapi.GetJobStatus.response = JOB_RUNNING

        # redistribute_config enables ignore_cache flag
        job_id = cluster.redistribute_config().id
        self.assertTrue(Job.objects.filter(id=job_id).exists())
        cluster = Cluster.objects.get(id=cluster.id)
        self.assertTrue(cluster.ignore_cache)
        self.assertTrue(cluster.last_job_id)
        self.assertTrue(
            Job.objects.filter(id=job_id).values()[0]['ignore_cache'])

        # finished job resets ignore_cache flag
        cluster.rapi.GetJobStatus.response = JOB
        cluster = Cluster.objects.get(id=cluster.id)
        self.assertFalse(cluster.ignore_cache)
        self.assertFalse(cluster.last_job_id)
        self.assertFalse(
            Job.objects.filter(id=job_id).values()[0]['ignore_cache'])
        self.assertTrue(Job.objects.get(id=job_id).finished)

        cluster.delete()
