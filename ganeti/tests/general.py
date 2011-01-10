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
from django.test import TestCase
from django.test.client import Client

from object_permissions import *


from ganeti.tests.rapi_proxy import RapiProxy, INFO, NODES, NODES_BULK
from ganeti import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Job = models.Job


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

        result = []

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # authorized user (non-admin)
        user.grant("admin", vm)
        user.save()
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        result.append(response)

        # authorized user (admin on one cluster)
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        result.append(response)

        # authorized user (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(status, response.status_code)
        self.assertEqual(mimetype, response['content-type'])
        self.assertTemplateUsed(response, template)
        result.append(response)

        clusters = result[0].context['cluster_list']
        self.assert_(cluster not in clusters)
        self.assertEqual(0, len(clusters))
        self.assert_(job not in result[0].context["job_errors"]) # due to no clusters
        self.assertEqual(0, len(result[0].context["job_errors"]))
        self.assertEqual(0, result[0].context["orphaned"])
        self.assertEqual(0, result[0].context["missing"])
        self.assertEqual(0, result[0].context["import_ready"])

        clusters = result[1].context['cluster_list']
        self.assert_(cluster in clusters)
        self.assertEqual(1, len(clusters))
        self.assert_(job in result[1].context["job_errors"])
        self.assertEqual(1, len(result[1].context["job_errors"]))
        self.assertEqual(1, result[1].context["orphaned"])
        self.assertEqual(1, result[1].context["missing"])
        self.assertEqual(2, result[1].context["import_ready"])

        clusters = result[2].context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 in clusters)
        self.assertEqual(2, len(clusters))
        self.assert_(job in result[2].context["job_errors"])
        self.assert_(job1 in result[2].context["job_errors"])
        self.assertEqual(2, len(result[2].context["job_errors"]))
        self.assertEqual(2, result[2].context["orphaned"])
        self.assertEqual(2, result[2].context["missing"])
        self.assertEqual(4, result[2].context["import_ready"])
