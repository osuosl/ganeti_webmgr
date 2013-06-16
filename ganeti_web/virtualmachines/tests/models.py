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

from utils import client
from utils.proxy import RapiProxy
from utils.proxy.constants import (INSTANCE, JOB, JOB_RUNNING,
                                   JOB_DELETE_SUCCESS)

from virtualmachines.models import VirtualMachine
from clusters.models import Cluster
from auth.models import ClusterUser
from jobs.models import Job

from ganeti_web import constants


__all__ = (
    'TestVirtualMachineModel',
    'VirtualMachineTestCaseMixin',
)


class VirtualMachineTestCaseMixin(object):
    def create_virtual_machine(self, cluster=None, hostname='vm1.example.bak'):
        if cluster is None:
            cluster = Cluster(hostname='test.example.bak', slug='OSL_TEST',
                              username='foo', password='bar')
        cluster.save()
        cluster.sync_nodes()
        vm = VirtualMachine(cluster=cluster, hostname=hostname)
        vm.save()
        return vm, cluster


class TestVirtualMachineModel(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        client.GanetiRapiClient = RapiProxy

    def test_save(self):
        """
        Test saving a VirtualMachine

        Verify:
            * VirtualMachine can be saved
            * VirtualMachine can be loaded
            * Hash is copied from cluster
        """
        vm, cluster = self.create_virtual_machine()
        self.assertTrue(vm.id)
        self.assertFalse(vm.error)
        self.assertEqual(vm.cluster_hash, cluster.hash)

        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertTrue(vm.info)
        self.assertFalse(vm.error)

        vm.delete()
        cluster.delete()

    def test_hash_update(self):
        """
        When cluster is saved hash for its VirtualMachines should be updated
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, cluster = self.create_virtual_machine(cluster,
                                                   'test2.example.bak')

        self.assertEqual(vm0.cluster_hash, cluster.hash)
        self.assertEqual(vm1.cluster_hash, cluster.hash)

        # change cluster's hash
        cluster.hostname = 'SomethingDifferent'
        cluster.save()
        vm0 = VirtualMachine.objects.get(pk=vm0.id)
        vm1 = VirtualMachine.objects.get(pk=vm1.id)
        self.assertEqual(vm0.cluster_hash, cluster.hash,
                         'VirtualMachine does not have updated cache')
        self.assertEqual(vm1.cluster_hash, cluster.hash,
                         'VirtualMachine does not have updated cache')

        vm0.delete()
        vm1.delete()
        cluster.delete()

    def test_parse_info(self):
        """
        Test parsing values from cached info

        Verifies:
            * mtime and ctime are parsed
            * ram, virtual_cpus, and disksize are parsed
        """
        vm, cluster = self.create_virtual_machine()
        vm.info = INSTANCE

        self.assertEqual(vm.ctime, datetime.fromtimestamp(1285799513.4741000))
        self.assertEqual(vm.mtime, datetime.fromtimestamp(1285883187.8692000))
        self.assertEqual(vm.ram, 512)
        self.assertEqual(vm.virtual_cpus, 2)
        self.assertEqual(vm.disk_size, 5120)

        vm.delete()
        cluster.delete()

    def test_update_owner_tag(self):
        """
        Test changing owner
        """
        vm, cluster = self.create_virtual_machine()

        owner0 = ClusterUser(id=74, name='owner0')
        owner1 = ClusterUser(id=21, name='owner1')
        owner0.save()
        owner1.save()

        # no owner
        vm.refresh()
        self.assertEqual([], vm.info['tags'])

        # setting owner
        vm.owner = owner0
        vm.save()
        self.assertEqual(['%s%s' % (constants.OWNER_TAG, owner0.id)],
                         vm.info['tags'])

        # changing owner
        vm.owner = owner1
        vm.save()
        self.assertEqual(['%s%s' % (constants.OWNER_TAG, owner1.id)],
                         vm.info['tags'])

        # setting owner to none
        vm.owner = None
        vm.save()
        self.assertEqual([], vm.info['tags'])

        owner0.delete()
        owner1.delete()
        vm.delete()
        cluster.delete()

    def test_start(self):
        """
        Test VirtualMachine.start()

        Verifies:
            * job is created
            * cache is disabled while job is running
            * cache is reenabled when job is finished
        """
        vm, cluster = self.create_virtual_machine()
        vm.rapi.GetJobStatus.response = JOB_RUNNING

        # reboot enables ignore_cache flag
        job = vm.startup()
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertTrue(Job.objects.filter(id=job.id).exists())
        self.assertTrue(vm.ignore_cache)
        self.assertTrue(vm.last_job_id)

        # finished job resets ignore_cache flag
        vm.rapi.GetJobStatus.response = JOB
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertFalse(vm.ignore_cache)
        self.assertFalse(vm.last_job_id)
        self.assertTrue(Job.objects.get(id=job.id).finished)

        job.delete()
        vm.delete()
        cluster.delete()

    def test_stop(self):
        """
        Test VirtualMachine.stop()

        Verifies:
            * job is created
            * cache is disabled while job is running
            * cache is reenabled when job is finished
        """
        vm, cluster = self.create_virtual_machine()
        vm.rapi.GetJobStatus.response = JOB_RUNNING

        # reboot enables ignore_cache flag
        job = vm.shutdown()
        self.assertTrue(Job.objects.filter(id=job.id).exists())
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertTrue(vm.ignore_cache)
        self.assertTrue(vm.last_job_id)
        self.assertTrue(
            Job.objects.filter(id=job.id).values()[0]['ignore_cache'])

        # finished job resets ignore_cache flag
        vm.rapi.GetJobStatus.response = JOB
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertFalse(vm.ignore_cache)
        self.assertFalse(vm.last_job_id)
        self.assertFalse(
            Job.objects.filter(id=job.id).values()[0]['ignore_cache'])
        self.assertTrue(Job.objects.get(id=job.id).finished)

        job.delete()
        vm.delete()
        cluster.delete()

    def test_reboot(self):
        """
        Test vm.reboot()

        Verifies:
            * job is created
            * cache is disabled while job is running
            * cache is reenabled when job is finished
        """
        vm, cluster = self.create_virtual_machine()
        vm.rapi.GetJobStatus.response = JOB_RUNNING

        # reboot enables ignore_cache flag
        job = vm.reboot()
        self.assertTrue(Job.objects.filter(id=job.id).exists())
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertTrue(vm.ignore_cache)
        self.assertTrue(vm.last_job_id)
        self.assertTrue(
            Job.objects.filter(id=job.id).values()[0]['ignore_cache'])

        # finished job resets ignore_cache flag
        vm.rapi.GetJobStatus.response = JOB
        self.assertTrue(Job.objects.filter(id=job.id).exists())
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assertFalse(vm.ignore_cache)
        self.assertFalse(vm.last_job_id)
        self.assertFalse(
            Job.objects.filter(id=job.id).values()[0]['ignore_cache'])
        self.assertTrue(Job.objects.get(id=job.id).finished)

        job.delete()
        vm.delete()
        cluster.delete()

    def test_load_pending_delete(self):
        """
        Tests loading a VM that has a pending delete

        Verifies:
            * The job is still running so the VM will be loaded
        """
        vm, cluster = self.create_virtual_machine()
        vm.rapi.GetJobStatus.response = JOB_RUNNING
        vm.refresh()
        vm.ignore_cache = True
        vm.pending_delete = True
        job = Job.objects.create(job_id=1, obj=vm, cluster_id=vm.cluster_id)
        vm.last_job = job
        vm.save()

        # Test loading vm, job is running so it should not be deleted yet
        vm = VirtualMachine.objects.get(pk=vm.pk)
        self.assertTrue(vm.id)
        self.assertTrue(vm.pending_delete)
        self.assertFalse(vm.deleted)

        job.delete()
        vm.delete()
        cluster.delete()

    def test_load_deleted(self):
        """
        Tests loading a VM that has a pending delete

        Verifies:
            * The Job is finished.  It will load the VM but it will be deleted
            and marked as such.
        """
        vm, cluster = self.create_virtual_machine()
        vm.rapi.GetJobStatus.response = JOB_RUNNING
        vm.refresh()
        vm.ignore_cache = True
        vm.pending_delete = True
        job = Job.objects.create(job_id=1, obj=vm, cluster_id=vm.cluster_id)
        vm.last_job = job
        vm.save()

        # Test loading vm, delete job is finished
        vm.rapi.GetJobStatus.response = JOB_DELETE_SUCCESS
        vm = VirtualMachine.objects.get(pk=vm.pk)
        self.assertTrue(vm.pending_delete)
        self.assertFalse(vm.last_job_id)
        self.assertFalse(VirtualMachine.objects.filter(pk=vm.pk).exists())

        job.delete()
        cluster.delete()
