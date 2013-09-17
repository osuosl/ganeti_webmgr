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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from django_test_tools.views import ViewTestMixin

from utils.proxy.constants import JOB_ERROR
from utils.models import SSHKey

from clusters.models import Cluster
from virtualmachines.models import VirtualMachine
from jobs.models import Job
from ..backend.queries import vm_qs_for_admins


__all__ = ('TestGeneralViews', 'TestOverviewVMSummary')


class TestGeneralViews(TestCase, ViewTestMixin):

    def setUp(self):
        self.tearDown()

        self.cluster = Cluster(hostname='test.example.test', slug='OSL_TEST')
        self.cluster.save()
        self.vm = VirtualMachine(hostname='vm1.example.bak',
                                 cluster=self.cluster)
        self.vm.save()

        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID = 1

        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.grant("admin", self.cluster)
        self.user1.grant("admin", self.vm)
        self.user1.save()
        self.user2 = User(id=4, username="tester2")
        self.user2.set_password("secret")
        self.user2.is_superuser = True
        self.user2.save()

        self.c = Client()

    def tearDown(self):
        SSHKey.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        Job.objects.all().delete()

    def test_view_overview(self):
        """
        Tests overview (status) page
        """
        # TODO: in future, add Ganeti errors checking

        cluster1 = Cluster(hostname='cluster1', slug='cluster1')
        cluster1.save()
        vm1 = VirtualMachine(hostname='vm2.example.bak', cluster=cluster1)
        vm1.save()
        job = Job(job_id=233, obj=self.vm, cluster=self.cluster,
                  finished="2011-01-07 21:59", status="error")
        job.save()
        job1 = Job(job_id=1234, obj=vm1, cluster=cluster1,
                   finished="2011-01-05 21:59", status="error")
        job1.save()
        job.rapi.GetJobStatus.response = JOB_ERROR

        url = "/"
        args = []
        template = "ganeti/overview.html"
        mimetype = "text/html; charset=utf-8"
        status = 200

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # authorized user (non-admin)
        self.user.grant("admin", self.vm)
        self.user.save()
        self.assertTrue(self.c.login(username=self.user.username,
                        password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(self.cluster not in clusters)
        self.assertEqual(0, len(clusters))
        self.assertEqual(0, response.context["orphaned"])
        self.assertEqual(0, response.context["missing"])
        self.assertEqual(0, response.context["import_ready"])

        # authorized user (admin on one cluster)
        self.assertTrue(self.c.login(username=self.user1.username,
                        password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(self.cluster in clusters)
        self.assertEqual(1, len(clusters))
        self.assertEqual(1, response.context["orphaned"])
        self.assertEqual(1, response.context["missing"])
        self.assertEqual(2, response.context["import_ready"])

        # authorized user (superuser)
        self.assertTrue(self.c.login(username=self.user2.username,
                        password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(self.cluster in clusters)
        self.assertTrue(cluster1 in clusters)
        self.assertEqual(2, len(clusters))
        self.assertEqual(2, response.context["orphaned"])
        self.assertEqual(2, response.context["missing"])
        self.assertEqual(4, response.context["import_ready"])

    def test_used_resources(self):
        """ tests the used_resources view """

        group0 = Group.objects.create(name='group0')
        group1 = Group.objects.create(name='group1')
        self.user.groups.add(group0)
        self.user1.groups.add(group1)

        url = "/used_resources/"
        args = {}
        template = "ganeti/overview/used_resources_data.html"
        mimetype = "text/html; charset=utf-8"

        # anonymous user
        response = self.c.get(url, args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # 404 - no id
        self.assertTrue(self.c.login(username=self.user.username,
                        password='secret'))
        response = self.c.get(url, {})
        self.assertEqual(404, response.status_code)

        # 404 - invalid id
        response = self.c.get(url, {'id': 1234567})
        self.assertEqual(404, response.status_code)

        # unauthorized user (different user)
        response = self.c.get(url, {'id': self.user2.get_profile().pk})
        self.assertEqual(403, response.status_code)

        # unauthorized user (in different group)
        self.assertTrue(self.c.login(username=self.user.username,
                        password='secret'))
        response = self.c.get(url, {'id': group1.organization.pk})
        self.assertEqual(403, response.status_code)

        # authorized user (same user)
        response = self.c.get(url, {'id': self.user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (in group)
        response = self.c.get(url, {'id': group0.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (superuser)
        self.assertTrue(self.c.login(username=self.user2.username,
                        password='secret'))
        response = self.c.get(url, {'id': self.user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (superuser)
        self.assertTrue(self.c.login(username=self.user2.username,
                        password='secret'))
        response = self.c.get(url, {'id': group1.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

    def test_view_ssh_keys(self):
        """ tests retrieving all sshkeys from the gwm instance """

        # add some keys
        SSHKey.objects.create(key="ssh-rsa test test@test", user=self.user)
        SSHKey.objects.create(key="ssh-dsa test asd@asd", user=self.user)
        SSHKey.objects.create(key="ssh-dsa test foo@bar", user=self.user1)

        self.user.revoke_all(self.vm)
        self.user.revoke_all(self.cluster)
        self.user1.revoke_all(self.vm)
        self.user1.revoke_all(self.cluster)
        self.user2.revoke_all(self.vm)
        self.user2.revoke_all(self.cluster)

        # get API key
        # import settings
        key = settings.WEB_MGR_API_KEY

        url = '/keys/%s/'
        args = (key,)

        # cluster without users who have admin perms
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 0)
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")

        # vm with users who have admin perms
        # grant admin permission to first user
        self.user.grant("admin", self.vm)
        self.user1.grant("admin", self.cluster)

        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 3)
        self.assertContains(response, "test@test", count=1)
        self.assertContains(response, "asd@asd", count=1)
        self.assertContains(response, "foo@bar", count=1)


class TestOverviewVMSummary(TestCase):
    def setUp(self):
        self.cluster = Cluster.objects.create(
            hostname='ganeti.example.org', slug='ganeti'
        )
        self.vm1 = VirtualMachine.objects.create(
            hostname='vm1', cluster=self.cluster, status='running'
        )
        self.vm2 = VirtualMachine.objects.create(
            hostname='vm2', cluster=self.cluster, status='running'
        )
        self.admin = User.objects.create_user('admin', password='secret')
        self.admin.grant('admin', self.cluster)
        self.standard = User.objects.create_user('standard', password='secret')

        self.summary_url = reverse("overview")

    def tearDown(self):
        self.cluster.delete()
        self.vm1.delete()
        self.vm2.delete()
        self.admin.delete()
        self.standard.delete()

    def test_admin_summary(self):
        """
        Tests that the vm summary for a user with admin permissions on a
        cluster is correct.
        """
        self.client.login(username=self.admin.username, password='secret')
        response = self.client.get(self.summary_url)
        vm_summary = response.context['vm_summary']
        vms = vm_qs_for_admins(self.admin)
        expected_summary = {
            unicode(self.cluster.hostname): {
                'total': len(vms),
                'running': len(vms.filter(status='running')),
                'cluster__slug': unicode(self.cluster.slug)
            }
        }
        self.assertEqual(vm_summary, expected_summary)

    def test_standard_summary_no_perms(self):
        """
        Tests that a user without any permissions does not have a VM Summary
        """
        self.client.login(username=self.standard.username, password='secret')
        response = self.client.get(self.summary_url)
        vm_summary = response.context['vm_summary']
        self.assertEqual(vm_summary, {})

    def test_standard_summary_vm_perms(self):
        """
        Tests that the vm summary for a user with admin permissions on a
        single VM (not cluster) is correct
        """
        self.standard.grant('admin', self.vm2)
        self.client.login(username=self.standard.username, password='secret')
        response = self.client.get(self.summary_url)
        vm_summary = response.context['vm_summary']
        vms = vm_qs_for_admins(self.standard)
        expected_summary = {
            unicode(self.cluster.hostname): {
                'total': len(vms),
                'running': len(vms.filter(status='running')),
                'cluster__slug': unicode(self.cluster.slug)
            }
        }
        self.assertEqual(vm_summary, expected_summary)
