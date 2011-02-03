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

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from ganeti.tests.call_proxy import CallProxy
from ganeti.tests.rapi_proxy import RapiProxy, JOB, JOB_RUNNING, JOB_ERROR
from ganeti import models
from ganeti.tests.virtual_machine import VirtualMachineTestCaseMixin


Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Job = models.Job


class TestJobMixin(VirtualMachineTestCaseMixin):

    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
        
        d = globals()
        d['vm'], d['cluster'] = self.create_virtual_machine()
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        Job.objects.all().delete()


class TestJobModel(TestJobMixin, TestCase):

    def test_trivial(self):
        """
        Test instantiating a Job
        """
        Job()
    
    def test_non_trivial(self):
        """
        Test instantiating a Job with extra parameters
        """
        return Job(job_id=1, cluster=cluster, obj=vm)
    
    def test_save(self):
        """
        Test saving a Job
        
        Verify:
            * Job can be saved
            * Job can be loaded
            * Hash is copied from cluster
        """
        job = Job(job_id=1, cluster=cluster, obj=vm)
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
        
        self.assertEqual(cluster.hash, job1.cluster_hash)
        self.assertEqual(cluster.hash, job2.cluster_hash)
        
        # change cluster's hash
        cluster.hostname = 'SomethingDifferent'        
        cluster.save()
        job1 = Job.objects.get(pk=job1.id)
        job2 = Job.objects.get(pk=job2.id)
        self.assertEqual(job1.cluster_hash, cluster.hash, 'Job does not have updated cache')
        self.assertEqual(job2.cluster_hash, cluster.hash, 'Job does not have updated cache')
    
    def test_cache_reset(self):
        """
        Tests that cache reset is working properly.
        
        Verifies:
            * when success or error status is achieved the job no longer updates
        """
        job = self.test_save()
        job.ignore_cache = True
        job.save()
        rapi = job.rapi
        rapi.GetJobStatus.response = JOB_RUNNING
        CallProxy.patch(job, '_refresh')
        
        # load with running status, should refresh
        job.load_info()
        self.assert_(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()
        
        # load again with running status, should refresh
        job.load_info()
        self.assert_(job.ignore_cache)
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
            * when success or error status is achieved the job no longer updates
        """
        job = self.test_save()
        job.ignore_cache = True
        job.save()
        rapi = job.rapi
        rapi.GetJobStatus.response = JOB_RUNNING
        CallProxy.patch(job, '_refresh')
        
        # load with running status, should refresh
        job.load_info()
        self.assert_(job.ignore_cache)
        job._refresh.assertCalled(self)
        job._refresh.reset()
        
        # load again with running status, should refresh
        job.load_info()
        self.assert_(job.ignore_cache)
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


class TestJobViews(TestJobMixin, TestCase):

    def setUp(self):
        super(TestJobViews, self).setUp()
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        
        d = globals()
        d['user'] = user
        d['c'] = Client()
    
    def tearDown(self):
        super(TestJobViews, self).tearDown()
        User.objects.all().delete()
    
    def test_clear_job(self):
        
        url = '/job/clear/'
        
        c_error = Job.objects.create(cluster=cluster, obj=cluster, job_id=1)
        c_error.info = JOB_ERROR
        c_error.save()
        c_error = Job.objects.get(pk=c_error.pk)
        self.assertFalse(c_error.cleared)
        
        vm_error = Job.objects.create(cluster=cluster, obj=vm, job_id=1)
        vm_error.info = JOB_ERROR
        vm_error.save()
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)
        
        # anonymous user
        response = c.post(url, {'id':vm_error.id}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url, {'id':vm_error.id})
        self.assertEqual(403, response.status_code)
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)
        
        # nonexisent error
        response = c.post(url, {'id':-1})
        self.assertEqual(404, response.status_code)
        
        # authorized for cluster (cluster admin)
        user.grant('admin', cluster)
        response = c.post(url, {'id':c_error.id})
        self.assertEqual(200, response.status_code)
        c_error = Job.objects.get(pk=c_error.pk)
        self.assert_(c_error.cleared)
        Job.objects.all().update(cleared=False)
        
        # authorized for vm (cluster admin)
        response = c.post(url, {'id':vm_error.id})
        self.assertEqual(200, response.status_code)
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assert_(vm_error.cleared)
        Job.objects.all().update(cleared=False)
        user.revoke_all(cluster)
        
        # authorized for vm (vm owner)
        vm.owner = user.get_profile()
        vm.save()
        response = c.post(url, {'id':vm_error.id})
        self.assertEqual(200, response.status_code)
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assert_(vm_error.cleared)
        Job.objects.all().update(cleared=False)
        vm.owner = None
        vm.save()
        
        # authorized for vm (superuser)
        user.is_superuser = True
        user.save()
        response = c.post(url, {'id':vm_error.id})
        self.assertEqual(200, response.status_code)
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.assert_(vm_error.cleared)
        Job.objects.all().update(cleared=False)