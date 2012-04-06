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

from ganeti_web.util.rapi_proxy import RapiProxy
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

        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()

        self.group = Group(name='testing_group')
        self.group.save()

        self.cluster0 = Cluster(hostname='test0', slug='OSL_TEST0')
        self.cluster0.save()
        self.cluster1 = Cluster(hostname='test1', slug='OSL_TEST1')
        self.cluster1.save()

        self.vm0 = VirtualMachine(hostname='vm0', cluster=self.cluster0)
        self.vm1 = VirtualMachine(hostname='vm1', cluster=self.cluster0,
                                  owner=self.user.get_profile())
        #self.vm2 = VirtualMachine(hostname='vm2', cluster=cluster0)
        self.vm3 = VirtualMachine(hostname='vm3', cluster=self.cluster1)
        self.vm4 = VirtualMachine(hostname='vm4', cluster=self.cluster1,
                                  owner=self.user.get_profile())
        #self.vm5 = VirtualMachine(hostname='vm5', cluster=cluster1)
        self.vm0.save()
        self.vm1.save()
        self.vm3.save()
        self.vm4.save()

        self.c = Client()
        self.owner = self.user.get_profile()

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
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        self.user.grant('admin', self.cluster0)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertEqual([(self.vm0.id, 'test0', 'vm0')], response.context['vms'])
        self.user.revoke_all(self.cluster0)

        # authorized get (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertEqual([(self.vm0.id, 'test0', 'vm0'), (self.vm3.id, 'test1', 'vm3')], response.context['vms'])
        self.user.is_superuser = False
        self.user.save()

        # POST - invalid vm
        self.user.grant('admin', self.cluster0)
        data = {'virtual_machines':[-1], 'owner':self.owner.id}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - invalid owner
        data = {'virtual_machines':[self.vm0.id], 'owner':-1}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[self.vm3.id], 'owner':self.owner.id}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/orphans.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':[self.vm0.id], 'owner':self.owner.id}
        response = self.c.post(url, data)
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
        self.cluster0.rapi.GetInstances.response = ['vm0','vm2']
        self.cluster1.rapi.GetInstances.response = ['vm3','vm5']

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        self.user.grant('admin', self.cluster0)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertEqual([('vm1','test0','vm1')], response.context['vms'])
        self.user.revoke_all(self.cluster0)

        # authorized get (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertEqual([('vm1','test0','vm1'), ('vm4','test1','vm4')], response.context['vms'])
        self.user.is_superuser = False
        self.user.save()

        # POST - invalid vm
        self.user.grant('admin', self.cluster0)
        data = {'virtual_machines':[-1]}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[self.vm3.hostname]}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':['vm1']}
        response = self.c.post(url, data)
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
        self.cluster0.rapi.GetInstances.response = ['vm0','vm2']
        self.cluster1.rapi.GetInstances.response = ['vm3','vm5']

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        response = self.c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized get (cluster admin perm)
        self.user.grant('admin', self.cluster0)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertEqual([('1:vm2','test0','vm2')], response.context['vms'])
        self.user.revoke_all(self.cluster0)

        # authorized get (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertEqual([('1:vm2','test0','vm2'), ('2:vm5','test1','vm5')], response.context['vms'])
        self.user.is_superuser = False
        self.user.save()

        # POST - invalid vm
        self.user.grant('admin', self.cluster0)
        data = {'virtual_machines':[-1]}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - invalid owner
        data = {'virtual_machines':[self.vm0.id], 'owner':-1}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - user does not have perms for cluster
        data = {'virtual_machines':[self.vm3.hostname], 'owner':self.owner.id}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertTrue(response.context['form'].errors)

        # POST - success
        data = {'virtual_machines':['1:vm2'], 'owner':self.owner.id}
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/importing/missing_db.html')
        self.assertFalse(response.context['form'].errors)
        self.assertEqual([], response.context['vms'])
        self.assertTrue(VirtualMachine.objects.filter(hostname='vm2').exists())
