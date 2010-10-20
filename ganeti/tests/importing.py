from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission

from ganeti.tests.rapi_proxy import RapiProxy, INSTANCES
from ganeti import models
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
        
        group = UserGroup(name='testing_group')
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
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('create_vm', Cluster)
        
        while INSTANCES:
            INSTANCES.pop()
        INSTANCES.extend(['vm0','vm2','vm3','vm5'])
    
    def tearDown(self):
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        Organization.objects.all().delete()
        Profile.objects.all().delete()
        UserGroup.objects.all().delete()
        User.objects.all().delete()
        while INSTANCES:
            INSTANCES.pop()
        INSTANCES.extend(['gimager.osuosl.bak', 'gimager2.osuosl.bak'])
    
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
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)
        
        # authorized get (cluster admin perm)
        user.grant('admin', cluster0)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assertEqual([(1, 'vm0')], response.context['vms'])
        user.revoke_all(cluster0)
        
        # authorized get (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assertEqual([(1, 'vm0'), (3, 'vm3')], response.context['vms'])
        user.is_superuser = False
        user.save()
        
        # POST - invalid vm
        user.grant('admin', cluster0)
        data = {'virtual_machines':[-1], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assert_(response.context['form'].errors)
        
        # POST - invalid owner
        data = {'virtual_machines':[vm0.id], 'owner':-1}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assert_(response.context['form'].errors)
        
        # POST - user does not have perms for cluster
        data = {'virtual_machines':[vm3.id], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assert_(response.context['form'].errors)
        
        # POST - success
        data = {'virtual_machines':[vm0.id], 'owner':owner.id}
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'importing/orphans.html')
        self.assertFalse(response.context['form'].errors)
        self.assertEqual([], response.context['vms'])