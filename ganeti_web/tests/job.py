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
from django.test.client import Client

from django_test_tools.views import ViewTestMixin
from django_test_tools.users import UserTestMixin

from ganeti_web.util.proxy import RapiProxy, CallProxy
from ganeti_web.util.proxy.constants import JOB, JOB_RUNNING, JOB_ERROR
from ganeti_web import models
from ganeti_web.tests.views.virtual_machine.base \
    import VirtualMachineTestCaseMixin


Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Job = models.Job


class TestJobMixin(VirtualMachineTestCaseMixin):

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy

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


class TestJobViews(TestJobMixin, TestCase, UserTestMixin, ViewTestMixin):

    def setUp(self):
        super(TestJobViews, self).setUp()

        self.create_standard_users()
        self.create_users(['user', 'vm_owner', 'cluster_admin', 'vm_admin'])

        # additional perms
        self.cluster_admin.grant('admin', self.cluster)
        self.vm_admin.grant('admin', self.vm)
        self.vm.owner = self.vm_owner.get_profile()
        self.vm.save()

        self.c = Client()

    def tearDown(self):
        # Tear down users.
        self.unauthorized.delete()
        self.superuser.delete()
        self.user.delete()
        self.vm_owner.delete()
        self.cluster_admin.delete()
        self.vm_admin.delete()

        super(TestJobViews, self).tearDown()

    def test_clear_job(self):

        url = '/cluster/%s/job/%s/clear/'

        c_error = Job.objects.create(cluster=self.cluster, obj=self.cluster,
                                     job_id=1)
        c_error.info = JOB_ERROR
        c_error.save()
        c_error = Job.objects.get(pk=c_error.pk)
        self.cluster.last_job = c_error
        self.cluster.ignore_cache = True
        self.cluster.save()
        vm_error = Job.objects.create(cluster=self.cluster, obj=self.vm,
                                      job_id=2)
        vm_error.info = JOB_ERROR
        vm_error.save()
        vm_error = Job.objects.get(pk=vm_error.pk)
        self.vm.last_job = vm_error
        self.vm.ignore_cache = True
        self.vm.save()

        # standard errors
        args = (self.cluster.slug, c_error.job_id)
        self.assert_standard_fails(url, args, method='post')

        # not authorized for cluster
        self.assert_403(url, args, users=[self.vm_admin, self.vm_owner],
                        data={'id': c_error.pk}, method='post')

        # does not clear job if it is not the the current job
        vm_error = Job.objects.create(cluster=self.cluster, obj=self.vm,
                                      job_id=3)
        vm_error.info = JOB_ERROR
        vm_error.save()
        vm_error = Job.objects.get(pk=vm_error.pk)
        vm_error2 = Job.objects.create(cluster=self.cluster, obj=self.vm,
                                       job_id=4)
        vm_error2.info = JOB_ERROR
        vm_error2.save()
        vm_error2 = Job.objects.get(pk=vm_error.pk)
        self.vm.last_job = vm_error
        self.vm.ignore_cache = True
        self.vm.save()

        self.c.post(url % (self.cluster.slug, vm_error2.job_id))
        updated = VirtualMachine.objects.filter(pk=self.vm.pk) \
            .values('last_job_id', 'ignore_cache')[0]
        self.assertEqual(vm_error.pk, updated['last_job_id'])
        self.assertTrue(updated['ignore_cache'])

    def test_clear_job_superuser(self):

        url = '/cluster/%s/job/%s/clear/'

        c_error = Job.objects.create(cluster=self.cluster, obj=self.cluster,
                                     job_id=1)
        c_error.info = JOB_ERROR
        c_error.save()
        c_error = Job.objects.get(pk=c_error.pk)
        self.cluster.last_job = c_error
        self.cluster.ignore_cache = True
        self.cluster.save()

        args = (self.cluster.slug, c_error.job_id)

        # authorized for cluster
        def tests(user, response):
            qs = Job.objects.filter(pk=c_error.pk)
            self.assertFalse(qs)
            updated = Cluster.objects.filter(pk=self.cluster.pk). \
                values('last_job_id', 'ignore_cache')[0]
            self.assertEqual(None, updated['last_job_id'])
            self.assertFalse(updated['ignore_cache'])
        self.assert_200(url, args, users=[self.superuser],
                        data={'id': c_error.pk}, tests=tests, method='post',
                        mime='application/json')

    def test_clear_job_authorized_cluster(self):

        url = '/cluster/%s/job/%s/clear/'

        c_error = Job.objects.create(cluster=self.cluster, obj=self.cluster,
                                     job_id=1)
        c_error.info = JOB_ERROR
        c_error.save()
        c_error = Job.objects.get(pk=c_error.pk)
        self.cluster.last_job = c_error
        self.cluster.ignore_cache = True
        self.cluster.save()

        args = (self.cluster.slug, c_error.job_id)

        # authorized for cluster
        def tests(user, response):
            qs = Job.objects.filter(pk=c_error.pk)
            self.assertFalse(qs)
            updated = Cluster.objects.filter(pk=self.cluster.pk) \
                .values('last_job_id', 'ignore_cache')[0]
            self.assertEqual(None, updated['last_job_id'])
            self.assertFalse(updated['ignore_cache'])
        self.assert_200(url, args, users=[self.cluster_admin],
                        data={'id': c_error.pk}, tests=tests, method='post',
                        mime='application/json')

    def test_clear_job_authorized_vm(self):

        url = '/cluster/%s/job/%s/clear/'

        # XXX ugh, sorry for this!
        for user in [self.superuser, self.cluster_admin, self.vm_admin,
                     self.vm_owner]:

            vm_error = Job.objects.create(cluster=self.cluster, obj=self.vm,
                                          job_id=2)
            vm_error.info = JOB_ERROR
            vm_error.save()
            vm_error = Job.objects.get(pk=vm_error.pk)
            self.vm.last_job = vm_error
            self.vm.ignore_cache = True
            self.vm.save()

            args = (self.cluster.slug, vm_error.job_id)

            def tests(user, response):
                qs = Job.objects.filter(pk=vm_error.pk)
                self.assertFalse(qs.exists(), "job error was not deleted")
                updated = VirtualMachine.objects.filter(pk=self.vm.pk) \
                    .values('last_job_id', 'ignore_cache')[0]
                self.assertEqual(None, updated['last_job_id'])
                self.assertFalse(updated['ignore_cache'])
            self.assert_200(url, args, users=[user], data={'id': vm_error.id},
                            tests=tests, method='post',
                            mime='application/json')

    def test_job_detail(self):
        """
        tests viewing job detail
        """

        c_error = Job.objects.create(cluster=self.cluster, obj=self.cluster,
                                     job_id=1)
        c_error.info = JOB_ERROR
        c_error.save()

        url = '/cluster/%s/job/%s/detail/'
        args = (self.cluster.slug, c_error.job_id)

        self.assert_standard_fails(url, args, authorized=False)
        self.assert_200(url, args, users=[self.superuser, self.cluster_admin],
                        template='ganeti/job/detail.html')
