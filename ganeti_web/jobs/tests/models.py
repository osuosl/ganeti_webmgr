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

from django.test import TestCase

from utils import client
from utils.proxy import RapiProxy, CallProxy
from utils.proxy.constants import JOB, JOB_RUNNING, JOB_ERROR
from virtualmachines.tests.base import VirtualMachineTestCaseMixin

from ..models import Job


class TestJobMixin(VirtualMachineTestCaseMixin):

    def setUp(self):
        client.GanetiRapiClient = RapiProxy

        self.vm, self.cluster = self.create_virtual_machine()

    def tearDown(self):
        self.vm.delete()
        self.cluster.delete()

    def test_trivial(self):
        """
        Test the setUp() and tearDown() methods.
        """

        pass


class TestJobModel(TestJobMixin, TestCase):

    def test_instantiation(self):
        """
        Test instantiating a Job
        """
        Job()

    def test_non_trivial(self):
        """
        Test instantiating a Job with extra parameters
        """
        return Job(job_id=1, cluster=self.cluster, obj=self.vm)

    def test_save(self):
        """
        Test saving a Job

        Verify:
            * Job can be saved
            * Job can be loaded
            * Hash is copied from cluster
        """
        job = Job(job_id=1, cluster=self.cluster, obj=self.vm)
        job.save()

        job = Job.objects.get(id=job.id)
        self.assertFalse(None, job.info)
        self.assertFalse(job.error)
        return job

    def test_hash_update(self):
        """
        When cluster is saved hash for its Jobs should be updated
        """
        job1 = self.test_save()
        job2 = self.test_save()

        self.assertEqual(self.cluster.hash, job1.cluster_hash)
        self.assertEqual(self.cluster.hash, job2.cluster_hash)

        # change cluster's hash
        self.cluster.hostname = 'SomethingDifferent'
        self.cluster.save()
        job1 = Job.objects.get(pk=job1.id)
        job2 = Job.objects.get(pk=job2.id)
        self.assertEqual(job1.cluster_hash, self.cluster.hash,
                         'Job does not have updated cache')
        self.assertEqual(job2.cluster_hash, self.cluster.hash,
                         'Job does not have updated cache')

    def test_cache_reset(self):
        """
        Tests that cache reset is working properly.

        Verifies:
            * when success or error status is achieved the
              job no longer updates
        """
        job = self.test_save()
        job.ignore_cache = True
        job.save()
        rapi = job.rapi
        rapi.GetJobStatus.response = JOB_RUNNING
        CallProxy.patch(job, '_refresh')

        # load with running status, should refresh
        job.load_info()
        self.assertTrue(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with running status, should refresh
        job.load_info()
        self.assertTrue(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with success status, should refresh and flip cache flag
        rapi.GetJobStatus.response = JOB
        job.load_info()
        self.assertFalse(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with success status, should use cache
        job.load_info()
        self.assertFalse(job.ignore_cache)
        job._refresh.assertNotCalled(self)

    def test_cache_reset_error(self):
        """
        Tests that cache reset is working properly.

        Verifies:
            * when success or error status is achieved
              the job no longer updates
        """
        job = self.test_save()
        job.ignore_cache = True
        job.save()
        rapi = job.rapi
        rapi.GetJobStatus.response = JOB_RUNNING
        CallProxy.patch(job, '_refresh')

        # load with running status, should refresh
        job.load_info()
        self.assertTrue(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with running status, should refresh
        job.load_info()
        self.assertTrue(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with success status, should refresh and flip cache flag
        rapi.GetJobStatus.response = JOB_ERROR
        job.load_info()
        self.assertFalse(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()

        # load again with success status, should use cache
        job.load_info()
        self.assertFalse(job.ignore_cache)
        job._refresh.assertNotCalled(self)


