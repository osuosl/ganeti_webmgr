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


from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client

from object_permissions import *

from ganeti_web.tests.rapi_proxy import RapiProxy
from ganeti_web import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Organization = models.Organization
Profile = models.Profile

__all__ = ('ImportViews', )

class ImportViews(TestCase):

    def setUp(self):
        self.tearDown()

        models.client.GanetiRapiClient = RapiProxy

        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()

        group = Group(name='testing_group')
        group.save()

        cluster0 = Cluster(hostname='test0', slug='OSL_TEST0')
        cluster0.save()
        cluster1 = Cluster(hostname='test1', slug='OSL_TEST1')
        cluster1.save()

        vm0 = VirtualMachine(hostname='vm0', cluster=cluster0)
        vm1 = VirtualMachine(hostname='vm1', cluster=cluster0, owner=user.get_profile())
        #vm2 = VirtualMachine(hostname='vm2', cluster=cluster0)
        vm3 = VirtualMachine(hostname='vm3', cluster=cluster1)
        vm4 = VirtualMachine(hostname='vm4', cluster=cluster1, owner=user.get_profile())
        #vm5 = VirtualMachine(hostname='vm5', cluster=cluster1)
        vm0.save()
        vm1.save()
        vm3.save()
        vm4.save()

        dict_ = globals()
        dict_['user'] = user
        dict_['group'] = group
        dict_['cluster0'] = cluster0
        dict_['cluster1'] = cluster1
        dict_['vm0'] = vm0
        dict_['vm1'] = vm1
        dict_['vm3'] = vm3
        dict_['vm4'] = vm4
        dict_['c'] = Client()
        dict_['owner'] = user.get_profile()

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        Organization.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_orphans_view(self):
        """
        Test orphans view
        """
        url='/import/orphans/'

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        user.grant('admin', cluster0)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertEqual([(vm0.id, 'test0', 'vm0')], response.context['vms'])
        user.revoke_all(cluster0)

        # authorized get (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertEqual([(vm0.id, 'test0', 'vm0'), (vm3.id, 'test1', 'vm3')], response.context['vms'])
        user.is_superuser = False
        user.save()

        # POST - invalid vm
        user.grant('admin', cluster0)
        data = {'virtual_machines':[-1], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - invalid owner
        data = {'virtual_machines':[vm0.id], 'owner':-1}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[vm3.id], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':[vm0.id], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertFalse(response.context['form'].errors)
        self.assertEqual([], response.context['vms'])

    def test_missing_ganeti(self):
        """
        Tests view for Virtual Machines missing from ganeti
        """
        url = '/import/missing/'
        cluster0.rapi.GetInstances.response = ['vm0','vm2']
        cluster1.rapi.GetInstances.response = ['vm3','vm5']

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        user.grant('admin', cluster0)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertEqual([('vm1','test0','vm1')], response.context['vms'])
        user.revoke_all(cluster0)

        # authorized get (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertEqual([('vm1','test0','vm1'), ('vm4','test1','vm4')], response.context['vms'])
        user.is_superuser = False
        user.save()

        # POST - invalid vm
        user.grant('admin', cluster0)
        data = {'virtual_machines':[-1]}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[vm3.hostname]}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':['vm1']}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertFalse(response.context['form'].errors)
        self.assertEqual([], response.context['vms'])

    def test_missing_db(self):
        """
        Tests view for Virtual Machines missing from database
        """
        url = '/import/missing_db/'
        cluster0.rapi.GetInstances.response = ['vm0','vm2']
        cluster1.rapi.GetInstances.response = ['vm3','vm5']

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        user.grant('admin', cluster0)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertEqual([('1:vm2','test0','vm2')], response.context['vms'])
        user.revoke_all(cluster0)

        # authorized get (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertEqual([('1:vm2','test0','vm2'), ('2:vm5','test1','vm5')], response.context['vms'])
        user.is_superuser = False
        user.save()

        # POST - invalid vm
        user.grant('admin', cluster0)
        data = {'virtual_machines':[-1]}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - invalid owner
        data = {'virtual_machines':[vm0.id], 'owner':-1}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[vm3.hostname], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':['1:vm2'], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertFalse(response.context['form'].errors)
        self.assertEqual([], response.context['vms'])
        self.assertTrue(VirtualMachine.objects.filter(hostname='vm2').exists())
