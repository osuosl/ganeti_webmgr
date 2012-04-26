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
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin
from ganeti_web.models import SSHKey

from object_permissions import get_user_perms

from ganeti_web.util.proxy import RapiProxy
from ganeti_web.util.proxy.constants import NODES, NODES_BULK
from ganeti_web import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Node = models.Node
Quota = models.Quota
Job = models.Job


__all__ = ['TestClusterViews', "TestClusterQuotaViews"]


class TestClusterViews(TestCase, ViewTestMixin, UserTestMixin):

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy

        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()

        group = Group(name='testing_group')
        group.save()

        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()

        self.create_standard_users()
        self.create_users(['cluster_admin'])
        self.cluster_admin.grant('admin', cluster)

        self.user = user
        self.group = group
        self.cluster = cluster
        self.c = Client()

    def tearDown(self):
        # Tear down users.
        self.user.delete()
        self.unauthorized.delete()
        self.superuser.delete()
        self.cluster_admin.delete()

        # Tear down the other stuff, too.
        self.group.delete()
        self.cluster.delete()

    def validate_get(self, url, args, template):
        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)

        # authorized user (perm)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password="secret"))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)

        # authorized user (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password="secret"))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)

    def test_trivial(self):
        """
        The setUp() and tearDown() methods should work.
        """

        pass

    def test_view_list(self):
        """
        Tests displaying the list of clusters
        """
        url = '/clusters/'

        # create extra user and tests
        cluster1 = Cluster(hostname='cluster1', slug='cluster1')
        cluster1.save()

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/list.html')
        clusters = response.context['cluster_list']
        self.assertFalse(clusters)

        # authorized permissions
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/list.html')
        clusters = response.context['cluster_list']
        self.assertTrue(self.cluster in clusters)
        self.assertTrue(cluster1 not in clusters)
        self.assertEqual(1, len(clusters))

        # authorized (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/list.html')
        clusters = response.context['cluster_list']
        self.assertTrue(self.cluster in clusters)
        self.assertTrue(cluster1 in clusters)
        self.assertEqual(2, len(clusters))

        cluster1.delete()

    def test_view_add(self):
        """
        Tests adding a new cluster
        """
        url = '/cluster/add/'

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized (GET)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/edit.html')

        data = dict(hostname='new-host3.hostname',
                    slug='new-host3',
                    port=5080,
                    description='testing editing clusters',
                    username='tester',
                    password = 'secret',
                    virtual_cpus=1,
                    disk=2,
                    ram=3
                    )

        # test error
        data_ = data.copy()
        del data_['hostname']
        response = self.c.post(url, data_)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/edit.html')

        # success
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/detail.html')
        cluster = response.context['cluster']
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))
        Cluster.objects.all().delete()



    def test_view_edit(self):
        """
        Tests editing a cluster
        """
        url = '/cluster/%s/edit/' % self.cluster.slug

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized (permission)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/edit.html')
        self.assertEqual(self.cluster, response.context['cluster'])

        # authorized (GET)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/edit.html')
        self.assertEqual(None, self.cluster.info)

        data = dict(hostname='new-host-1.hostname',
                    slug='new-host-1',
                    port=5080,
                    description='testing editing clusters',
                    username='tester',
                    password = 'secret',
                    confirm_password = 'secret',
                    virtual_cpus=1,
                    disk=2,
                    ram=3
                    )
        # error
        data_ = data.copy()
        del data_['hostname']
        response = self.c.post(url, data_)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/edit.html')

        # success
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/detail.html')
        cluster = response.context['cluster']
        self.assertNotEqual(None, cluster.info)
        del data_['confirm_password']
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))

    def test_view_delete_anonymous(self):
        """
        Random people shouldn't be able to delete clusters.
        """

        url = '/cluster/%s/edit/' % self.cluster.slug

        response = self.c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_delete_unauthorized(self):
        """
        Unauthorized people shouldn't be able to delete clusters.
        """

        url = '/cluster/%s/edit/' % self.cluster.slug

        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.delete(url)
        self.assertEqual(403, response.status_code)

    def test_view_delete_authorized(self):
        """
        Users with admin on the cluster should be able to delete the cluster.
        """

        cluster = Cluster(hostname='test.cluster.bak', slug='cluster1')
        cluster.save()
        url = '/cluster/%s/edit/' % cluster.slug

        self.user.grant('admin', cluster)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals('1', response.content)
        self.assertFalse(Cluster.objects.all().filter(id=cluster.id).exists())

    def test_view_delete_superuser(self):
        """
        Superusers can delete clusters.
        """

        cluster = Cluster(hostname='test.cluster.bak', slug='cluster1')
        cluster.save()
        url = '/cluster/%s/edit/' % cluster.slug

        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals('1', response.content)
        self.assertFalse(Cluster.objects.all().filter(id=cluster.id).exists())

    def test_view_detail(self):
        """
        Tests displaying detailed view for a Cluster
        """
        url = '/cluster/%s/'
        args = self.cluster.slug

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code) # Ticket 6891

        # invalid cluster
        response = self.c.get(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)

        # authorized (permission)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/detail.html')

        # authorized (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/detail.html')

    def test_view_users(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/users/"
        args = self.cluster.slug
        self.validate_get(url, args, 'ganeti/cluster/users.html')

    def test_view_virtual_machines(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/virtual_machines/"
        args = self.cluster.slug
        self.validate_get(url, args, 'ganeti/virtual_machine/table.html')

    def test_view_nodes(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/nodes/"
        args = self.cluster.slug
        self.cluster.rapi.GetNodes.response = NODES_BULK
        self.validate_get(url, args, 'ganeti/node/table.html')
        self.cluster.rapi.GetNodes.response = NODES

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or Group
        """
        url = '/cluster/%s/permissions/'
        args = self.cluster.slug

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # valid GET authorized user (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # no user or group
        data = {
            'permissions': ['admin'],
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # both user and group
        data = {
            'permissions': ['admin'],
            'group': self.group.id,
            'user': self.user.id,
            'cluster': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - user
        data = {
            'permissions': [],
            'user': self.user.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - group
        data = {
            'permissions': [],
            'group': self.group.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])

        # valid POST user has permissions
        self.user.grant('create_vm', self.cluster)
        data = {
            'permissions': ["admin"],
            'user': self.user.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/user_row.html')
        self.assertTrue(self.user.has_perm('admin', self.cluster))
        self.assertFalse(self.user.has_perm('create_vm', self.cluster))

        # valid POST group has permissions
        self.group.grant('create_vm', self.cluster)
        data = {
            'permissions': ["admin"],
            'group': self.group.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/group_row.html')
        self.assertEqual(['admin'], self.group.get_perms(self.cluster))

    def test_view_object_log(self):
        """
        Tests view for cluster object log:

        Verifies:
            * view can be loaded
            * cluster specific log actions can be rendered properly
        """
        url = "/cluster/%s/object_log/"
        args = (self.cluster.slug,)
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users=[self.superuser, self.cluster_admin])

    def test_view_user_permissions(self):
        """
        Tests updating users permissions

        Verifies:
            * anonymous user returns 403
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * invalid group returns 404
            * missing user and group returns error as json
            * GET returns html for form
            * If user/group has permissions no html is returned
            * If user/group has no permissions a json response of -1 is returned
        """
        args = (self.cluster.slug, self.user.id)
        args_post = self.cluster.slug
        url = "/cluster/%s/permissions/user/%s"
        url_post = "/cluster/%s/permissions/"

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % ("DOES_NOT_EXIST", self.user.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # valid GET authorized user (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid user
        response = self.c.get(url % (self.cluster.slug, -1))
        self.assertEqual(404, response.status_code)

        # invalid user (POST)
        self.user.grant('create_vm', self.cluster)
        data = {
            'permissions': ['admin'],
            'user': -1,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no user (POST)
        # XXX double-grant?
        self.user.grant('create_vm', self.cluster)
        data = {
            'permissions': ['admin'],
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST user has permissions
        # XXX triple-grant?!
        self.user.grant('create_vm', self.cluster)
        data = {
            'permissions': ['admin'],
            'user': self.user.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/user_row.html')
        self.assertTrue(self.user.has_perm('admin', self.cluster))
        self.assertFalse(self.user.has_perm('create_vm', self.cluster))

        # add quota to the user
        user_quota = {'default':0, 'ram':51, 'virtual_cpus':10, 'disk':3000}
        quota = Quota(cluster=self.cluster, user=self.user.get_profile())
        quota.__dict__.update(user_quota)
        quota.save()
        self.assertEqual(user_quota,
                         self.cluster.get_quota(self.user.get_profile()))

        # valid POST user has no permissions left
        data = {
            'permissions': [],
            'user': self.user.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(self.user, self.cluster))
        # XXX this is too hardcoded and can spuriously fail
        self.assertEqual('"user_2"', response.content)

        # quota should be deleted (and showing default)
        self.assertEqual(1,
                         self.cluster.get_quota(self.user.get_profile())['default'])
        self.assertFalse(self.user.get_profile().quotas.all().exists())

        # no permissions specified - user with no quota
        # XXX quadra-grant!!!
        self.user.grant('create_vm', self.cluster)
        self.cluster.set_quota(self.user.get_profile(), None)
        data = {
            'permissions': [],
            'user': self.user.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # quota should be deleted (and showing default)
        self.assertEqual(1,
                         self.cluster.get_quota(self.user.get_profile())['default'])
        self.assertFalse(self.user.get_profile().quotas.all().exists())

    def test_view_group_permissions(self):
        """
        Test editing Group permissions on a Cluster
        """
        args = (self.cluster.slug, self.group.id)
        args_post = self.cluster.slug
        url = "/cluster/%s/permissions/group/%s"
        url_post = "/cluster/%s/permissions/"

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % ("DOES_NOT_EXIST", self.group.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.cluster)

        # valid GET authorized user (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid group
        response = self.c.get(url % (self.cluster.slug, 0))
        self.assertEqual(404, response.status_code)

        # invalid group (POST)
        data = {
            'permissions': ['admin'],
            'group': -1,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no group (POST)
        data = {
            'permissions': ['admin'],
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST group has permissions
        self.group.grant('create_vm', self.cluster)
        data = {
            'permissions': ['admin'],
            'group': self.group.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/group_row.html')
        self.assertEqual(['admin'], self.group.get_perms(self.cluster))

        # add quota to the group
        user_quota = {'default':0, 'ram':51, 'virtual_cpus':10, 'disk':3000}
        quota = Quota(cluster=self.cluster, user=self.group.organization)
        quota.__dict__.update(user_quota)
        quota.save()
        self.assertEqual(user_quota,
                         self.cluster.get_quota(self.group.organization))

        # valid POST group has no permissions left
        data = {
            'permissions': [],
            'group': self.group.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], self.group.get_perms(self.cluster))
        self.assertEqual('"group_%s"' % self.group.id, response.content)

        # quota should be deleted (and showing default)
        self.assertEqual(1,
                         self.cluster.get_quota(self.group.organization)['default'])
        self.assertFalse(self.group.organization.quotas.all().exists())

        # no permissions specified - user with no quota
        self.group.grant('create_vm', self.cluster)
        self.cluster.set_quota(self.group.organization, None)
        data = {
            'permissions': [],
            'group': self.group.id,
            'obj': self.cluster.pk,
        }
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # quota should be deleted (and showing default)
        self.assertEqual(1,
                         self.cluster.get_quota(self.group.organization)['default'])
        self.assertFalse(self.group.organization.quotas.all().exists())

    def test_sync_virtual_machines_in_edit_view(self):
        """
        Test if sync_virtual_machines is run after editing a cluster
        for the second time
        """
        #configuring stuff needed to test edit view
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        self.cluster.virtual_machines.all().delete()
        url = '/cluster/%s/edit/' % self.cluster.slug

        data = dict(hostname='new-host-1.hostname',
                    slug='new-host-1',
                    port=5080,
                    description='testing editing clusters',
                    username='tester',
                    password = 'secret',
                    virtual_cpus=1,
                    disk=2,
                    ram=3
                    )

        # run view once to create cluster
        self.c.post(url, data, follow=True)

        # ensure there are VMs ready for sync
        self.cluster.virtual_machines.all().delete()

        #run view_edit again..
        self.c.post(url, data, follow=True)

        # assert that no VMs were created
        self.assertFalse(self.cluster.virtual_machines.all().exists())

    def test_view_ssh_keys(self):
        """
        Test getting SSH keys belonging to users, who have admin permission on
        specified cluster
        """
        vm = VirtualMachine.objects.create(cluster=self.cluster,
                                           hostname='vm1.osuosl.bak')

        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()

        # add some keys
        SSHKey.objects.create(key="ssh-rsa test test@test", user=self.user)
        SSHKey.objects.create(key="ssh-dsa test asd@asd", user=self.user)
        SSHKey.objects.create(key="ssh-dsa test foo@bar", user=user1)

        # get API key
        # XXX agh oh god what why are you doing this argfl
        import settings
        key = settings.WEB_MGR_API_KEY

        url = '/cluster/%s/keys/%s/'
        args = (self.cluster.slug, key)

        self.assert_standard_fails(url, args, login_required=False, authorized=False)

        # cluster without users who have admin perms
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 0 )
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")

        # vm with users who have admin perms
        # grant admin permission to first user
        # XXX ...but we aren't using these users anywhere after this...
        self.user.grant("admin", vm)
        user1.grant("admin", self.cluster)

        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 3 )
        self.assertContains(response, "test@test", count=1)
        self.assertContains(response, "asd@asd", count=1)
        self.assertContains(response, "foo@bar", count=1)

        user1.delete()

    def test_view_redistribute_config(self):
        """
        Tests cluster's config redistribution
        """

        url = '/cluster/%s/redistribute-config/' % self.cluster.slug

        # anonymous user
        response = self.c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.unauthorized.username,
                                     password='secret'))
        response = self.c.post(url)
        self.assertEqual(403, response.status_code)

        # authorized (permission)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertTrue('status' in response.content)
        self.assertTrue(Cluster.objects.filter(id=self.cluster.id).exists())
        self.user.revoke('admin', self.cluster)

        # recreate cluster
        self.cluster.save()

        # authorized (GET)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertTrue('status' in response.content)
        self.assertTrue(Cluster.objects.filter(id=self.cluster.id).exists())

class TestClusterQuotaViews(TestCase, ViewTestMixin, UserTestMixin):
    """
    Test quota views on clusters.
    """

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy

        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()

        group = Group(name='testing_group')
        group.save()

        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()

        self.create_standard_users()
        self.create_users(['cluster_admin'])
        self.cluster_admin.grant('admin', cluster)

        self.user = user
        self.group = group
        self.cluster = cluster
        self.c = Client()

    def tearDown(self):
        # Tear down users.
        self.user.delete()
        self.superuser.delete()
        self.cluster_admin.delete()

        # Tear down the other stuff, too.
        self.group.delete()
        self.cluster.delete()

    def validate_anonymous(self, cluster_user):
        url = '/cluster/%s/quota/%s'
        args = (self.cluster.slug, cluster_user.id)

        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def validate_unauthorized(self, cluster_user):
        url = '/cluster/%s/quota/%s'
        args = (self.cluster.slug, cluster_user.id)

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

    def validate_quota(self, cluster_user, template):
        """
        Generic tests for validating quota views

        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * missing user returns error as json
            * GET returns html for form
            * successful POST returns html for user row
            * successful DELETE removes user quota
        """

        default_quota = {'default':1, 'ram':1, 'virtual_cpus':None, 'disk':3}
        user_quota = {'default':0, 'ram':4, 'virtual_cpus':5, 'disk':None}
        user_unlimited = {'default':0, 'ram':None, 'virtual_cpus':None, 'disk':None}
        self.cluster.__dict__.update(default_quota)
        self.cluster.save()

        args = (self.cluster.slug, cluster_user.id)
        args_post = self.cluster.slug
        url = '/cluster/%s/quota/%s'
        url_post = '/cluster/%s/quota/'

        # valid GET authorized user (perm)
        self.assertTrue(self.c.login(username=self.cluster_admin.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/cluster/quota.html')

        # valid GET authorized user (superuser)
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'ganeti/cluster/quota.html')

        # no user (GET)
        response = self.c.get(url_post % args_post)
        self.assertEqual(404, response.status_code)

        # no user (POST)
        data = {'ram':'', 'virtual_cpus':'', 'disk':''}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])

        # valid POST - setting unlimited values (nones)
        data = {'user':cluster_user.id, 'ram':'', 'virtual_cpus':'', 'disk':''}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_unlimited, self.cluster.get_quota(cluster_user))
        query = Quota.objects.filter(cluster=self.cluster, user=cluster_user)
        self.assertTrue(query.exists())

        # valid POST - setting values
        data = {'user':cluster_user.id, 'ram':4, 'virtual_cpus':5, 'disk':''}
        response = self.c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_quota, self.cluster.get_quota(cluster_user))
        self.assertTrue(query.exists())

        # valid POST - same as default values (should delete)
        data = {'user':cluster_user.id, 'ram':1, 'disk':3}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, self.cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())

        # valid POST - same as default values (should do nothing)
        data = {'user':cluster_user.id, 'ram':1, 'disk':3}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, self.cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())

        # valid POST - setting implicit unlimited (values are excluded)
        data = {'user':cluster_user.id}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_unlimited, self.cluster.get_quota(cluster_user))
        self.assertTrue(query.exists())

        # valid DELETE - returns to default values
        data = {'user':cluster_user.id, 'delete':True}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, self.cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())

    def test_trivial(self):
        """
        Verify that setUp() and tearDown() work.
        """

        pass

    def test_view_user_quota(self):
        """
        Tests updating users quota
        """

        self.validate_quota(self.user.get_profile(),
                            template='ganeti/cluster/user_row.html')

    def test_view_group_quota(self):
        """
        Tests updating a Group's quota
        """

        self.validate_quota(self.group.organization,
                            template='ganeti/cluster/group_row.html')

    def test_quota_nonexistent(self):
        """
        Quotas for nonexistent clusters should result in not-found errors.
        """

        response = self.c.get("/cluster/%s/user/quota/?user=%s" %
                         ("DOES_NOT_EXIST", self.user.id))
        self.assertEqual(404, response.status_code)

    def test_user_quota_anonymous(self):
        self.validate_anonymous(self.user.get_profile())

    def test_user_quota_unauthorized(self):
        self.validate_unauthorized(self.user.get_profile())

    def test_group_quota_anonymous(self):
        self.validate_anonymous(self.group.organization)

    def test_group_quota_unauthorized(self):
        self.validate_unauthorized(self.group.organization)
