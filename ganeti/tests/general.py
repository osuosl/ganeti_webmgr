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


from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client

from object_permissions import *


from ganeti.tests.rapi_proxy import RapiProxy, INFO, NODES, NODES_BULK
from ganeti import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Job = models.Job

from ganeti.views.general import update_vm_counts

__all__ = ('TestGeneralViews', )


class TestGeneralViews(TestCase):
    
    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.tearDown()

        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()
        vm = VirtualMachine(hostname='vm1.osuosl.bak', cluster=cluster)
        vm.save()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
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
        Cluster.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        Job.objects.all().delete()
        self.clear_cache()
    
    def clear_cache(self):
        # delete caches to make sure we don't get any unused states
        cache.delete('cluster_admin_0')
        cache.delete('cluster_admin_1')
        cache.delete('cluster_admin_2')
        cache.delete('cluster_admin_3')
        cache.delete('cluster_admin_4')

    def test_view_overview(self):
        """
        Tests overview (status) page
        """
        # TODO: in future, add Ganeti errors checking

        cluster1 = Cluster(hostname='cluster1', slug='cluster1')
        cluster1.save()
        vm1 = VirtualMachine(hostname='vm2.osuosl.bak', cluster=cluster1)
        vm1.save()
        job = Job(job_id=233, obj=vm, cluster=cluster,
                finished="2011-01-07 21:59", status="error")
        job.save()
        job1 = Job(job_id=1234, obj=vm1, cluster=cluster1,
                finished="2011-01-05 21:59", status="error")
        job1.save()

        url = "/"
        args = []
        template = "overview.html"
        mimetype = "text/html; charset=utf-8"
        status = 200

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # authorized user (non-admin)
        self.clear_cache()
        user.grant("admin", vm)
        user.save()
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assert_(cluster not in clusters)
        self.assertEqual(0, len(clusters))
        self.assert_((False, job) in response.context["errors"]) # due to no clusters
        self.assertFalse((False, job1) in response.context["errors"]) # due to no clusters
        self.assertEqual(1, len(response.context["errors"]))
        self.assertEqual(0, response.context["orphaned"])
        self.assertEqual(0, response.context["missing"])
        self.assertEqual(0, response.context["import_ready"])

        # authorized user (admin on one cluster)
        self.clear_cache()
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assertEqual(1, len(clusters))
        self.assert_((False, job) in response.context["errors"])
        self.assertFalse((False, job1) in response.context["errors"]) # due to no clusters
        self.assertEqual(1, len(response.context["errors"]))
        self.assertEqual(1, response.context["orphaned"])
        self.assertEqual(1, response.context["missing"])
        self.assertEqual(2, response.context["import_ready"])

        # authorized user (superuser)
        self.clear_cache()
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 in clusters)
        self.assertEqual(2, len(clusters))
        self.assert_((False, job) in response.context["errors"])
        self.assert_((False, job1) in response.context["errors"])
        self.assertEqual(2, len(response.context["errors"]))
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
        template = "overview/used_resources_data.html"
        mimetype = "text/html; charset=utf-8"

        # anonymous user
        response = c.get(url, args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # 404 - no id
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url, {})
        self.assertEqual(404, response.status_code)
        
        # 404 - invalid id
        response = c.get(url, {'id':1234567})
        self.assertEqual(404, response.status_code)
        
        # unauthorized user (different user)
        response = c.get(url, {'id':user2.get_profile().pk})
        self.assertEqual(403, response.status_code)
        
        # unauthorized user (in different group)
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url, {'id':group1.organization.pk})
        self.assertEqual(403, response.status_code)
        
        # authorized user (same user)
        response = c.get(url, {'id':user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (in group)
        response = c.get(url, {'id':group0.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url, {'id':user.get_profile().pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url, {'id':group1.organization.pk})
        self.assertEqual(200, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
    
    def test_cluster_admin_counts_cache(self):
        """ tests the cache for the admin cluster counts on the status page
        these tests will fail if cache is not configured
        
        Verifies:
            * existing values are updated
            * any of the dict keys can be updated
            * keys not in the cache are discarded
        """
        ids = ['cluster_admin_0', 'cluster_admin_1', 'cluster_admin_2']
        
        data = {
            'cluster_admin_0':{'orphaned':1,'missing':2,'ready_to_import':3},
            'cluster_admin_1':{'orphaned':4,'missing':5,'ready_to_import':6}
        }
        cache.set_many(data)
        
        update = {
            0:4,
            1:5,
            3:6,
        }
        
        # update orphaned
        update_vm_counts('orphaned', update)
        cached = cache.get_many(ids)
        self.assert_('cluster_admin_0' in cached)
        self.assert_('cluster_admin_1' in cached)
        self.assertFalse('cluster_admin_2' in cached)
        self.assertEqual(5, cached['cluster_admin_0']['orphaned'])
        self.assertEqual(2, cached['cluster_admin_0']['missing'])
        self.assertEqual(3, cached['cluster_admin_0']['ready_to_import'])
        self.assertEqual(9, cached['cluster_admin_1']['orphaned'])
        self.assertEqual(5, cached['cluster_admin_1']['missing'])
        self.assertEqual(6, cached['cluster_admin_1']['ready_to_import'])
        
        # update orphaned
        update_vm_counts('missing', update)
        cached = cache.get_many(ids)
        self.assert_('cluster_admin_0' in cached)
        self.assert_('cluster_admin_1' in cached)
        self.assertFalse('cluster_admin_2' in cached)
        self.assertEqual(5, cached['cluster_admin_0']['orphaned'])
        self.assertEqual(6, cached['cluster_admin_0']['missing'])
        self.assertEqual(3, cached['cluster_admin_0']['ready_to_import'])
        self.assertEqual(9, cached['cluster_admin_1']['orphaned'])
        self.assertEqual(10, cached['cluster_admin_1']['missing'])
        self.assertEqual(6, cached['cluster_admin_1']['ready_to_import'])
        
        # update ready_to_import
        update_vm_counts('ready_to_import', update)
        cached = cache.get_many(ids)
        self.assert_('cluster_admin_0' in cached)
        self.assert_('cluster_admin_1' in cached)
        self.assertFalse('cluster_admin_2' in cached)
        self.assertEqual(5, cached['cluster_admin_0']['orphaned'])
        self.assertEqual(6, cached['cluster_admin_0']['missing'])
        self.assertEqual(7, cached['cluster_admin_0']['ready_to_import'])
        self.assertEqual(9, cached['cluster_admin_1']['orphaned'])
        self.assertEqual(10, cached['cluster_admin_1']['missing'])
        self.assertEqual(11, cached['cluster_admin_1']['ready_to_import'])

    def test_vm_counts(self):
        """
        Tests the helper function get_vm_counts.
        """
        cluster1 = Cluster(hostname="cluster1")
        cluster2 = Cluster(hostname="cluster2")
        vm11 = VirtualMachine(cluster=cluster1, hostname="vm11")
        vm12 = VirtualMachine(cluster=cluster1, hostname="vm12")
        vm13 = VirtualMachine(cluster=cluster1, hostname="vm13")
        vm21 = VirtualMachine(cluster=cluster2, hostname="vm21")
        vm22 = VirtualMachine(cluster=cluster2, hostname="vm22")
        vm23 = VirtualMachine(cluster=cluster2, hostname="vm23")
