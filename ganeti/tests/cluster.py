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

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin
from ganeti.models import SSHKey, Profile

from object_permissions import *

from ganeti.tests.rapi_proxy import RapiProxy, INFO, NODES, NODES_BULK, JOB_RUNNING, JOB
from ganeti import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Node = models.Node
Quota = models.Quota
Job = models.Job


__all__ = ('TestClusterViews', 'TestClusterModel')


global user, user1, group, cluster_admin, superuser
global cluster, c


class TestClusterModel(TestCase):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
    
    def tearDown(self):
        Profile.objects.all().delete()
        User.objects.all().delete()
        Quota.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()

    def test_trivial(self):
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
        cluster = Cluster()
        cluster.save()
        self.assert_(cluster.hash)
        
        cluster = Cluster(hostname='foo.fake.hostname', slug='different')
        cluster.save()
        self.assert_(cluster.hash)
    
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
        
        self.assertEqual(cluster.ctime, datetime.fromtimestamp(1270685309.818239))
        self.assertEqual(cluster.mtime, datetime.fromtimestamp(1283552454.2998919))
    
    def test_get_quota(self):
        """
        Tests cluster.get_quota() method
        
        Verifies:
            * if no user is passed, return default quota values
            * if user has quota, return values from Quota
            * if user doesn't have quota, return default cluster values
        """
        default_quota = {'default':1, 'ram':1, 'virtual_cpus':None, 'disk':3}
        user_quota = {'default':0, 'ram':4, 'virtual_cpus':5, 'disk':None}
        
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
    
    def test_set_quota(self):
        """
        Tests cluster.set_quota()
        
        Verifies:
            * passing values with no quota, creates a new quota object
            * passing values with an existing quota, updates it.
            * passing a None with an existing quota deletes it
            * passing a None with no quota, does nothing
        """
        default_quota = {'default':1,'ram':1, 'virtual_cpus':None, 'disk':3}
        user_quota = {'default':0, 'ram':4, 'virtual_cpus':5, 'disk':None}
        user_quota2 = {'default':0, 'ram':7, 'virtual_cpus':8, 'disk':9}
        
        cluster = Cluster(hostname='foo.fake.hostname')
        cluster.__dict__.update(default_quota)
        cluster.save()
        user = User(username='tester')
        user.save()
        
        # create new quota
        cluster.set_quota(user.get_profile(), user_quota)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assert_(query.exists())
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
    
    def test_sync_virtual_machines(self):
        """
        Tests synchronizing cached virtuals machines (stored in db) with info
        the ganeti cluster is storing
        
        Verifies:
            * VMs no longer in ganeti are deleted
            * VMs missing from the database are added
        """
        cluster = Cluster(hostname='ganeti.osuosl.test')
        cluster.save()
        vm_missing = 'gimager.osuosl.bak'
        vm_current = VirtualMachine(cluster=cluster, hostname='gimager2.osuosl.bak')
        vm_removed = VirtualMachine(cluster=cluster, hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()
        
        cluster.sync_virtual_machines()
        self.assert_(VirtualMachine.objects.get(cluster=cluster, hostname=vm_missing), 'missing vm was not created')
        self.assert_(VirtualMachine.objects.get(cluster=cluster, hostname=vm_current.hostname), 'previously existing vm was not created')
        self.assert_(VirtualMachine.objects.filter(cluster=cluster, hostname=vm_removed.hostname), 'vm not present in ganeti was not removed from db, even though remove flag was false')
        
        cluster.sync_virtual_machines(True)
        self.assertFalse(VirtualMachine.objects.filter(cluster=cluster, hostname=vm_removed.hostname), 'vm not present in ganeti was not removed from db')
    
    def test_sync_nodes(self):
        """
        Tests synchronizing cached Nodes (stored in db) with info
        the ganeti cluster is storing
        
        Verifies:
            * Node no longer in ganeti are deleted
            * Nodes missing from the database are added
        """
        cluster = Cluster.objects.create(hostname='ganeti.osuosl.test')
        node_missing = 'gtest1.osuosl.bak'
        node_current = Node.objects.create(cluster=cluster, hostname='gtest2.osuosl.bak')
        node_removed = Node.objects.create(cluster=cluster, hostname='does.not.exist.org')
        
        cluster.sync_nodes()
        self.assert_(Node.objects.get(cluster=cluster, hostname=node_missing), 'missing node was not created')
        self.assert_(Node.objects.get(cluster=cluster, hostname=node_current.hostname), 'previously existing node was not created')
        self.assert_(Node.objects.filter(cluster=cluster, hostname=node_removed.hostname), 'node not present in ganeti was not removed from db, even though remove flag was false')
        
        cluster.sync_nodes(True)
        self.assertFalse(Node.objects.filter(cluster=cluster, hostname=node_removed.hostname), 'node not present in ganeti was not removed from db')


    def test_missing_in_database(self):
        """
        Tests missing_in_ganeti property
        """
        cluster = Cluster(hostname='ganeti.osuosl.test')
        cluster.save()
        vm_current = VirtualMachine(cluster=cluster, hostname='gimager2.osuosl.bak')
        vm_removed = VirtualMachine(cluster=cluster, hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()
        
        self.assertEqual([u'gimager.osuosl.bak'], cluster.missing_in_db)

    def test_missing_in_ganeti(self):
        """
        Tests missing_in_ganeti property
        """
        cluster = Cluster(hostname='ganeti.osuosl.test')
        cluster.save()
        vm_current = VirtualMachine(cluster=cluster, hostname='gimager2.osuosl.bak')
        vm_removed = VirtualMachine(cluster=cluster, hostname='does.not.exist.org')
        vm_current.save()
        vm_removed.save()
        
        self.assertEqual([u'does.not.exist.org'], cluster.missing_in_ganeti)

    def test_available_ram(self):
        """
        Tests that the available_ram property returns the correct values
        """
        c = Cluster.objects.create(hostname='ganeti.osuosl.test')
        c2 = Cluster.objects.create(hostname='ganeti2.osuosl.test', slug='argh')
        node = Node.objects.create(cluster=c, hostname='node.osuosl.test')
        node1 = Node.objects.create(cluster=c2, hostname='node1.osuosl.test')

        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='foo', ram=123, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='bar', ram=456, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xoo', ram=789, status='admin_down')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xar', ram=234, status='stopped')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='boo', status='running')
        VirtualMachine.objects.create(cluster=c2, primary_node=node1, hostname='gar', ram=888, status='running')
        VirtualMachine.objects.create(cluster=c2, primary_node=node1, hostname='yoo', ram=999, status='admin_down')

        # test with no nodes, should result in zeros since nodes info isn't cached yet
        ram = c.available_ram
        self.assertEqual(0, ram['free'])
        self.assertEqual(0, ram['total'])

        # force refresh of nodes and rerun test for real values
        node.refresh()
        node1.refresh()
        ram = c.available_ram
        self.assertEqual(9999, ram['total'])
        self.assertEqual(9420, ram['free'])

    
    def test_available_disk(self):
        """
        Tests that the available_disk property returns the correct values
        """
        c = Cluster.objects.create(hostname='ganeti.osuosl.test')
        c2 = Cluster.objects.create(hostname='ganeti2.osuosl.test', slug='argh')
        node = Node.objects.create(cluster=c, hostname='node.osuosl.test')
        node1 = Node.objects.create(cluster=c2, hostname='node1.osuosl.test')
        
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='foo', disk_size=123, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node,hostname='bar', disk_size=456, status='running')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xoo', disk_size=789, status='admin_down')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='xar', disk_size=234, status='stopped')
        VirtualMachine.objects.create(cluster=c, primary_node=node, hostname='boo', status='running')
        VirtualMachine.objects.create(cluster=c2, primary_node=node1, hostname='gar', disk_size=888, status='running')
        VirtualMachine.objects.create(cluster=c2, primary_node=node1, hostname='yoo', disk_size=999, status='admin_down')

        # test with no nodes, should result in zeros since nodes info isn't cached yet
        disk = c.available_disk
        self.assertEqual(0, disk['free'])
        self.assertEqual(0, disk['total'])

        # force refresh of nodes and rerun test for real values
        node.refresh()
        node1.refresh()
        disk = c.available_disk
        self.assertEqual(6666, disk['total'])
        self.assertEqual(5064, disk['free'])

    def test_redistribute_config(self):
        """
        Test Cluster.redistribute_config()

        Verifies:
            * job is created
            * cache is disabled while job is running
            * cache is reenabled when job is finished
        """
        cluster = Cluster.objects.create(hostname='ganeti.osuosl.test')
        cluster.rapi.GetJobStatus.response = JOB_RUNNING

        # redistribute_config enables ignore_cache flag
        job_id = cluster.redistribute_config().id
        self.assert_(Job.objects.filter(id=job_id).exists())
        cluster = Cluster.objects.get(id=cluster.id)
        self.assert_(cluster.ignore_cache)
        self.assert_(cluster.last_job_id)
        self.assert_(Job.objects.filter(id=job_id).values()[0]['ignore_cache'])

        # finished job resets ignore_cache flag
        cluster.rapi.GetJobStatus.response = JOB
        cluster = Cluster.objects.get(id=cluster.id)
        self.assertFalse(cluster.ignore_cache)
        self.assertFalse(cluster.last_job_id)
        self.assertFalse(Job.objects.filter(id=job_id).values()[0]['ignore_cache'])
        self.assert_(Job.objects.get(id=job_id).finished)


class TestClusterViews(TestCase, ViewTestMixin, UserTestMixin):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()

        group = Group(name='testing_group')
        group.save()
        
        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()

        self.create_standard_users(globals())
        self.create_users(['cluster_admin'], globals())
        cluster_admin.grant('admin', cluster)
        
        dict_ = globals()
        dict_['user'] = user
        dict_['user1'] = user1
        dict_['group'] = group
        dict_['cluster'] = cluster
        dict_['c'] = Client()

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Quota.objects.all().delete()
        Cluster.objects.all().delete()
        Group.objects.all().delete()
        User.objects.all().delete()

    def validate_get(self, url, args, template):
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        # authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)

    def validate_get_configurable(self, url, args, template=False,
            mimetype=False, status=False, perms=[]):
        """
        More configurable version of validate_get.
        Additional arguments (only if set) affects only authorized user test.

        @template: used template
        @mimetype: returned mimetype
        @status:   returned Http status code
        @perms:    set of perms granted on authorized user

        @return    response content
        """
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        if args:
            response = c.get(url % "DOES_NOT_EXIST")
            self.assertEqual(404, response.status_code)
        
        result = []

        # authorized user (perm)
        if perms:
            for perm in perms:
                grant(user, perm, cluster)
        response = c.get(url % args)
        if status:
            self.assertEqual(status, response.status_code)
        if mimetype:
            self.assertEqual(mimetype, response['content-type'])
        if template:
            self.assertTemplateUsed(response, template)

        result.append(response)
        
        # authorized user (superuser)
        user.revoke_all(cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        if status:
            self.assertEqual(200, response.status_code)
        if mimetype:
            self.assertEqual(mimetype, response['content-type'])
        if template:
            self.assertTemplateUsed(response, template)

        result.append(response)

        return result

    def test_view_list(self):
        """
        Tests displaying the list of clusters
        """
        url = '/clusters/'
        
        # create extra user and tests
        user2 = User(id=4, username='tester2', is_superuser=True)
        user2.set_password('secret')
        user2.save()
        cluster1 = Cluster(hostname='cluster1', slug='cluster1')
        cluster2 = Cluster(hostname='cluster2', slug='cluster2')
        cluster3 = Cluster(hostname='cluster3', slug='cluster3')
        cluster1.save()
        cluster2.save()
        cluster3.save()
        
        # grant some perms
        user1.grant('admin', cluster)
        user1.grant('create_vm', cluster1)
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assertFalse(clusters)
        
        # authorized permissions
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 not in clusters)
        self.assertEqual(1, len(clusters))
        
        # authorized (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 in clusters)
        self.assert_(cluster2 in clusters)
        self.assert_(cluster3 in clusters)
        self.assertEqual(4, len(clusters))

    def test_view_add(self):
        """
        Tests adding a new cluster
        """
        url = '/cluster/add/'
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        
        # authorized (GET)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/edit.html')
        
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
        
        # test required fields
        required = ['hostname', 'port']
        for property in required:
            data_ = data.copy()
            del data_[property]
            response = c.post(url, data_)
            self.assertEqual(200, response.status_code)
            self.assertEquals('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'cluster/edit.html')
        
        # test not-requireds
        non_required = ['slug','description','virtual_cpus','disk','ram']
        for property in non_required:
            data_ = data.copy()
            del data_[property]
            response = c.post(url, data_, follow=True)
            self.assertEqual(200, response.status_code)
            self.assertEquals('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'cluster/detail.html')
            cluster = response.context['cluster']
            for k, v in data_.items():
                self.assertEqual(v, getattr(cluster, k))
            Cluster.objects.all().delete()
        
        
        # success
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')
        cluster = response.context['cluster']
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))
        Cluster.objects.all().delete()
        
        # success without username or password
        data_ = data.copy()
        del data_['username']
        del data_['password']
        response = c.post(url, data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')
        cluster = response.context['cluster']
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))
        Cluster.objects.all().delete()
        
        #test username/password/confirm_password relationships
        relation = ['username', 'password']
        for property in relation:
            data_ = data.copy()
            del data_[property]
            response = c.post(url, data_, follow=True)
            self.assertEqual(200, response.status_code)
            self.assertEquals('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'cluster/edit.html')
        
        # test unique fields
        response = c.post(url, data)
        for property in ['hostname','slug']:
            data_ = data.copy()
            data_[property] = 'different'
            response = c.post(url, data_)
            self.assertEqual(200, response.status_code)
            self.assertEquals('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'cluster/edit.html')
    
    def test_view_edit(self):
        """
        Tests editing a cluster
        """
        cluster = globals()['cluster']
        url = '/cluster/%s/edit/' % cluster.slug
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        
        # authorized (permission)
        user.grant('admin', cluster)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/edit.html')
        self.assertEqual(cluster, response.context['cluster'])
        user.revoke('admin', cluster)
        
        # authorized (GET)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/edit.html')
        self.assertEqual(None, cluster.info)
        
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
        
        # success
        data_ = data.copy()
        response = c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')
        cluster = response.context['cluster']
        self.assertNotEqual(None, cluster.info)
        del data_['confirm_password']
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))

    def test_view_delete_anonymous(self):
        """
        Random people shouldn't be able to delete clusters.
        """

        cluster = Cluster(hostname='test.cluster.bak', slug='cluster1')
        cluster.save()
        url = '/cluster/%s/edit/' % cluster.slug

        response = c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_delete_unauthorized(self):
        """
        Unauthorized people shouldn't be able to delete clusters.
        """

        cluster = Cluster(hostname='test.cluster.bak', slug='cluster1')
        cluster.save()
        url = '/cluster/%s/edit/' % cluster.slug

        self.assert_(c.login(username=user.username, password='secret'))
        response = c.delete(url)
        self.assertEqual(403, response.status_code)

    def test_view_delete_authorized(self):
        """
        Users with admin on the cluster should be able to delete the cluster.
        """

        cluster = Cluster(hostname='test.cluster.bak', slug='cluster1')
        cluster.save()
        url = '/cluster/%s/edit/' % cluster.slug

        user.grant('admin', cluster)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.delete(url, follow=True)
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

        user.is_superuser = True
        user.save()
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.delete(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals('1', response.content)
        self.assertFalse(Cluster.objects.all().filter(id=cluster.id).exists())

    def test_view_detail(self):
        """
        Tests displaying detailed view for a Cluster
        """
        url = '/cluster/%s/'
        args = cluster.slug
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')

    def test_view_users(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/users/"
        args = cluster.slug
        self.validate_get(url, args, 'cluster/users.html')

    def test_view_virtual_machines(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/virtual_machines/"
        args = cluster.slug
        self.validate_get(url, args, 'virtual_machine/table.html')

    def test_view_nodes(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/nodes/"
        args = cluster.slug
        cluster.rapi.GetNodes.response = NODES_BULK
        self.validate_get(url, args, 'node/table.html')
        cluster.rapi.GetNodes.response = NODES

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or Group
        """
        url = '/cluster/%s/permissions/'
        args = cluster.slug
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # no user or group
        data = {'permissions':['admin'], 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # both user and group
        data = {'permissions':['admin'], 'group':group.id, 'user':user1.id, 'cluster':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - user
        data = {'permissions':[], 'user':user1.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - group
        data = {'permissions':[], 'group':group.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST user has permissions
        user1.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'user':user1.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assert_(user1.has_perm('admin', cluster))
        self.assertFalse(user1.has_perm('create_vm', cluster))
        
        # valid POST group has permissions
        group.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'group':group.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(['admin'], group.get_perms(cluster))

    def test_view_object_log(self):
        """
        Tests view for cluster object log:

        Verifies:
            * view can be loaded
            * cluster specific log actions can be rendered properly
        """
        url = "/cluster/%s/object_log/"
        args = (cluster.slug,)
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users=[superuser, cluster_admin])

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
        args = (cluster.slug, user1.id)
        args_post = cluster.slug
        url = "/cluster/%s/permissions/user/%s"
        url_post = "/cluster/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, -1))
        self.assertEqual(404, response.status_code)
        
        # invalid user (POST)
        user1.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'user':-1, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no user (POST)
        user1.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST user has permissions
        user1.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'user':user1.id, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assert_(user1.has_perm('admin', cluster))
        self.assertFalse(user1.has_perm('create_vm', cluster))
        
        # add quota to the user
        user_quota = {'default':0, 'ram':51, 'virtual_cpus':10, 'disk':3000}
        quota = Quota(cluster=cluster, user=user1.get_profile())
        quota.__dict__.update(user_quota)
        quota.save()
        self.assertEqual(user_quota, cluster.get_quota(user1.get_profile()))
        
        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(user, cluster))
        self.assertEqual('"user_3"', response.content)
        
        # quota should be deleted (and showing default)
        self.assertEqual(1, cluster.get_quota(user1.get_profile())['default'])
        self.assertFalse(user1.get_profile().quotas.all().exists())
        
        # no permissions specified - user with no quota
        user1.grant('create_vm', cluster)
        cluster.set_quota(user1.get_profile(), None)
        data = {'permissions':[], 'user':user1.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # quota should be deleted (and showing default)
        self.assertEqual(1, cluster.get_quota(user1.get_profile())['default'])
        self.assertFalse(user1.get_profile().quotas.all().exists())

    def test_view_group_permissions(self):
        """
        Test editing Group permissions on a Cluster
        """
        args = (cluster.slug, group.id)
        args_post = cluster.slug
        url = "/cluster/%s/permissions/group/%s"
        url_post = "/cluster/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", group.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        
        # invalid group
        response = c.get(url % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # invalid group (POST)
        data = {'permissions':['admin'], 'group':-1, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no group (POST)
        data = {'permissions':['admin'], 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST group has permissions
        group.grant('create_vm', cluster)
        data = {'permissions':['admin'], 'group':group.id, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(['admin'], group.get_perms(cluster))
        
        # add quota to the group
        user_quota = {'default':0, 'ram':51, 'virtual_cpus':10, 'disk':3000}
        quota = Quota(cluster=cluster, user=group.organization)
        quota.__dict__.update(user_quota)
        quota.save()
        self.assertEqual(user_quota, cluster.get_quota(group.organization))
        
        # valid POST group has no permissions left
        data = {'permissions':[], 'group':group.id, 'obj':cluster.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], group.get_perms(cluster))
        self.assertEqual('"group_%s"'%group.id, response.content)
        
        # quota should be deleted (and showing default)
        self.assertEqual(1, cluster.get_quota(group.organization)['default'])
        self.assertFalse(group.organization.quotas.all().exists())
        
        # no permissions specified - user with no quota
        group.grant('create_vm', cluster)
        cluster.set_quota(group.organization, None)
        data = {'permissions':[], 'group':group.id, 'obj':cluster.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # quota should be deleted (and showing default)
        self.assertEqual(1, cluster.get_quota(group.organization)['default'])
        self.assertFalse(group.organization.quotas.all().exists())
    
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
        cluster.__dict__.update(default_quota)
        cluster.save()
        
        args = (cluster.slug, cluster_user.id)
        args_post = cluster.slug
        url = '/cluster/%s/quota/%s'
        url_post = '/cluster/%s/quota/'
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/user/quota/?user=%s" % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # no user (GET)
        response = c.get(url_post % args_post)
        self.assertEqual(404, response.status_code)
        
        # no user (POST)
        data = {'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST - setting unlimited values (nones)
        data = {'user':cluster_user.id, 'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        query = Quota.objects.filter(cluster=cluster, user=cluster_user)
        self.assert_(query.exists())
        
        # valid POST - setting values
        data = {'user':cluster_user.id, 'ram':4, 'virtual_cpus':5, 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_quota, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid POST - same as default values (should delete)
        data = {'user':cluster_user.id, 'ram':1, 'disk':3}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())
        
        # valid POST - same as default values (should do nothing)
        data = {'user':cluster_user.id, 'ram':1, 'disk':3}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())
        
        # valid POST - setting implicit unlimited (values are excluded)
        data = {'user':cluster_user.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid DELETE - returns to default values
        data = {'user':cluster_user.id, 'delete':True}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, template)
        self.assertEqual(default_quota, cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())
    
    def test_view_user_quota(self):
        """
        Tests updating users quota
        """
        self.validate_quota(user1.get_profile(), template='cluster/user_row.html')
    
    def test_view_group_quota(self):
        """
        Tests updating a Group's quota
        """
        self.validate_quota(group.organization, template='cluster/group_row.html')

    def test_sync_virtual_machines_in_edit_view(self):
        """
        Test if sync_virtual_machines is run after editing a cluster
        for the second time
        """
        #configuring stuff needed to test edit view
        user.is_superuser = True
        user.save()
        self.assert_(c.login(username=user.username, password='secret'))
        cluster.virtual_machines.all().delete()
        url = '/cluster/%s/edit/' % cluster.slug

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
        c.post(url, data, follow=True)
        
        # ensure there are VMs ready for sync
        cluster.virtual_machines.all().delete()
        
        #run view_edit again..
        c.post(url, data, follow=True)
        
        # assert that no VMs were created
        self.assertFalse(cluster.virtual_machines.all().exists())
    
    def test_view_ssh_keys(self):
        """
        Test getting SSH keys belonging to users, who have admin permission on
        specified cluster
        """
        vm = VirtualMachine.objects.create(cluster=cluster, hostname='vm1.osuosl.bak')

        # add some keys
        SSHKey.objects.create(key="ssh-rsa test test@test", user=user)
        SSHKey.objects.create(key="ssh-dsa test asd@asd", user=user)
        SSHKey.objects.create(key="ssh-dsa test foo@bar", user=user1)

        # get API key
        import settings, json
        key = settings.WEB_MGR_API_KEY

        url = '/cluster/%s/keys/%s/'
        args = (cluster.slug, key)

        self.assert_standard_fails(url, args, login_required=False, authorized=False)

        # cluster without users who have admin perms
        response = c.get(url % args)
        self.assertEqual(200, response.status_code )
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 0 )
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")

        # vm with users who have admin perms
        # grant admin permission to first user
        user.grant("admin", vm)
        user1.grant("admin", cluster)

        response = c.get(url % args)
        self.assertEqual(200, response.status_code )
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 3 )
        self.assertContains(response, "test@test", count=1)
        self.assertContains(response, "asd@asd", count=1)
        self.assertContains(response, "foo@bar", count=1)

    def test_view_redistribute_config(self):
        """
        Tests cluster's config redistribution
        """
        cluster = globals()['cluster']
        url = '/cluster/%s/redistribute-config/' % cluster.slug

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.delete(url)
        self.assertEqual(403, response.status_code)

        # authorized (permission)
        user.grant('admin', cluster)
        response = c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assert_('status' in response.content)
        self.assert_(Cluster.objects.filter(id=cluster.id).exists())
        user.revoke('admin', cluster)

        # recreate cluster
        cluster.save()

        # authorized (GET)
        user.is_superuser = True
        user.save()
        response = c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assert_('status' in response.content)
        self.assert_(Cluster.objects.filter(id=cluster.id).exists())