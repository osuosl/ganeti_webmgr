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

from ganeti_web.backend.queries import vm_qs_for_admins
from ganeti_web.models import SSHKey
from ganeti_web.util.proxy import RapiProxy
from ganeti_web.util.proxy.constants import JOB_ERROR
from ganeti_web import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Job = models.Job


__all__ = ('TestGeneralViews', 'TestOverviewVMSummary')


class TestGeneralViews(TestCase, ViewTestMixin):

    def setUp(self):
        self.tearDown()

        models.client.GanetiRapiClient = RapiProxy

        cluster = Cluster(hostname='test.example.test', slug='OSL_TEST')
        cluster.save()
        vm = VirtualMachine(hostname='vm1.example.bak', cluster=cluster)
        vm.save()

        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID = 1

        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.grant("admin", cluster)
        user1.grant("admin", vm)
        user1.save()
        user2 = User(id=4, username="tester2")
        user2.set_password("secret")
        user2.is_superuser = True
        user2.save()

        dict_ = globals()
        dict_['user'] = user
        dict_['user1'] = user1
        dict_['user2'] = user2
        dict_['cluster'] = cluster
        dict_['vm'] = vm
        dict_['c'] = Client()

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
        job = Job(job_id=233, obj=vm, cluster=cluster,
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
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # authorized user (non-admin)
        user.grant("admin", vm)
        user.save()
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(cluster not in clusters)
        self.assertEqual(0, len(clusters))
        self.assertEqual(0, response.context["orphaned"])
        self.assertEqual(0, response.context["missing"])
        self.assertEqual(0, response.context["import_ready"])

        # authorized user (admin on one cluster)
        self.assertTrue(c.login(username=user1.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(cluster in clusters)
        self.assertEqual(1, len(clusters))
        self.assertEqual(1, response.context["orphaned"])
        self.assertEqual(1, response.context["missing"])
        self.assertEqual(2, response.context["import_ready"])

        # authorized user (superuser)
        self.assertTrue(c.login(username=user2.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assertTrue(cluster in clusters)
        self.assertTrue(cluster1 in clusters)
        self.assertEqual(2, len(clusters))
        self.assertEqual(2, response.context["orphaned"])
        self.assertEqual(2, response.context["missing"])
        self.assertEqual(4, response.context["import_ready"])

    def test_used_resources(self):
        """ tests the used_resources view """

        group0 = Group.objects.create(name='group0')
        group1 = Group.objects.create(name='group1')
        user.groups.add(group0)
        user1.groups.add(group1)

        url = "/used_resources/"
        args = {}
        template = "ganeti/overview/used_resources_data.html"
        mimetype = "text/html; charset=utf-8"

        # anonymous user
        response = c.get(url, args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # 404 - no id
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url, {})
        self.assertEqual(404, response.status_code)

        # 404 - invalid id
        response = c.get(url, {'id': 1234567})
        self.assertEqual(404, response.status_code)

        # unauthorized user (different user)
        response = c.get(url, {'id': user2.get_profile().pk})
        self.assertEqual(403, response.status_code)

        # unauthorized user (in different group)
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url, {'id': group1.organization.pk})
        self.assertEqual(403, response.status_code)

        # authorized user (same user)
        response = c.get(url, {'id': user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (in group)
        response = c.get(url, {'id': group0.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (superuser)
        self.assertTrue(c.login(username=user2.username, password='secret'))
        response = c.get(url, {'id': user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (superuser)
        self.assertTrue(c.login(username=user2.username, password='secret'))
        response = c.get(url, {'id': group1.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)

    def test_view_ssh_keys(self):
        """ tests retrieving all sshkeys from the gwm instance """

        # add some keys
        SSHKey.objects.create(key="ssh-rsa test test@test", user=user)
        SSHKey.objects.create(key="ssh-dsa test asd@asd", user=user)
        SSHKey.objects.create(key="ssh-dsa test foo@bar", user=user1)

        user.revoke_all(vm)
        user.revoke_all(cluster)
        user1.revoke_all(vm)
        user1.revoke_all(cluster)
        user2.revoke_all(vm)
        user2.revoke_all(cluster)

        # get API key
        import settings
        key = settings.WEB_MGR_API_KEY

        url = '/keys/%s/'
        args = (key,)

        self.assert_standard_fails(url, args, login_required=False,
                                   authorized=False)

        # cluster without users who have admin perms
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 0)
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")

        # vm with users who have admin perms
        # grant admin permission to first user
        user.grant("admin", vm)
        user1.grant("admin", cluster)

        response = c.get(url % args)
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
