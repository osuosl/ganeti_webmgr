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

from ganeti_web.util.rapi_proxy import RapiProxy
from ganeti_web import models
VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
ClusterUser = models.ClusterUser
Profile = models.Profile
Organization = models.Organization
Quota = models.Quota

__all__ = ('TestClusterUser',)


class TestClusterUser(TestCase):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy

    def tearDown(self):
        Quota.objects.all().delete()
        Profile.objects.all().delete()
        ClusterUser.objects.all().delete()
        User.objects.all().delete()
        Organization.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_user_signal(self):
        """
        Test signals related to User:
        
        Verifies:
            * profile is created/deleted with user
        """
        user = User(username='tester')
        user.save()
        
        # profile created
        profile = user.get_profile()
        self.assertTrue(profile, 'profile was not created')
        
        # profile deleted
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile.id).exists())
    
    def test_group_signal(self):
        """
        Test signals related to User:
        
        Verifies:
            * organization is created/deleted with Group
        """
        group = Group(name='tester')
        group.save()
        
        # org created
        org = group.organization
        self.assertTrue(group.organization, 'profile was not created')
        
        # org deleted
        group.delete()
        self.assertFalse(Organization.objects.filter(id=org.id).exists())
    
    def test_casting_profile(self):
        """
        Tests casting ClusterUser into Profile
        """
        user = User(username='tester')
        user.save()
        
        cluster_user = ClusterUser.objects.all()[0]
        profile = cluster_user.cast()
        
        self.assertTrue(isinstance(profile, (Profile,)))
    
    def test_casting_organization(self):
        """
        Tests casting ClusterUser into an Organization
        """
        group = Group(name='tester')
        group.save()
        
        cluster_user = ClusterUser.objects.all()[0]
        organization = cluster_user.cast()
        
        self.assertTrue(isinstance(organization, (Organization,)))
    
    def test_used_resources(self):
        """
        Tests retrieving dictionary of resources used by a cluster user
        """
        c1 = Cluster(hostname="testing1", slug="test1")
        c2 = Cluster(hostname="testing2", slug="test2")
        c3 = Cluster(hostname="testing3", slug="test3")
        user = User(username="owner")
        quota = {"disk": 26, "ram":6, "virtual_cpus":14}

        for i in (c1, c2, c3, user): i.save()

        owner = user.get_profile()
        c1.set_quota(owner, quota)
        #c2.set_quota(owner, quota)
        c3.set_quota(owner, quota)
        
        # test used_resources returns zeros for no values
        result = owner.used_resources(cluster=c1)
        self.assertEqual(0, result['ram'])
        self.assertEqual(0, result['disk'])
        self.assertEqual(0, result['virtual_cpus'])
        
        vm11 = VirtualMachine(hostname="1one", owner=owner, cluster=c1, status="running")
        vm21 = VirtualMachine(hostname="2one", owner=owner, cluster=c2, status="running")
        vm31 = VirtualMachine(hostname="3one", owner=owner, cluster=c2, status="running")

        vm12 = VirtualMachine(hostname="1two", owner=owner, cluster=c1, status="running",
                ram=1, virtual_cpus=3, disk_size=6)
        vm22 = VirtualMachine(hostname="2two", owner=owner, cluster=c2, status="running",
                ram=1, virtual_cpus=3, disk_size=6)
        vm32 = VirtualMachine(hostname="3two", owner=owner, cluster=c3, status="running",
                ram=1, virtual_cpus=3, disk_size=6)

        vm13 = VirtualMachine(hostname="1three", owner=owner, cluster=c1, status="stopped",
                ram=1, virtual_cpus=3, disk_size=6)
        vm23 = VirtualMachine(hostname="2three", owner=owner, cluster=c2, status="stopped",
                ram=1, virtual_cpus=3, disk_size=6)
        vm33 = VirtualMachine(hostname="3three", owner=owner, cluster=c3, status="stopped",
                ram=1, virtual_cpus=3, disk_size=6)
        
        for i in (vm11, vm12, vm13, vm21, vm22, vm23, vm31, vm32, vm33):
            i.save()
        
        # multiple clusters - every VM
        result = owner.used_resources(cluster=None, only_running=False)
        self.assertTrue(c1.id in result.keys())
        self.assertTrue(c2.id in result.keys())
        self.assertTrue(c3.id in result.keys())
        self.assertEqual(result[c1.id]["disk"], 12)
        self.assertEqual(result[c1.id]["ram"], 2)
        self.assertEqual(result[c1.id]["virtual_cpus"], 6)
        self.assertEqual(result[c1.id], result[c3.id])
        
        # multiple clusters - only running VMs
        result = owner.used_resources(cluster=None, only_running=True)
        self.assertTrue(c1.id in result.keys())
        self.assertTrue(c2.id in result.keys())
        self.assertTrue(c3.id in result.keys())
        self.assertEqual(result[c1.id]["disk"], 12)
        self.assertEqual(result[c1.id]["ram"], 1)
        self.assertEqual(result[c1.id]["virtual_cpus"], 3)
        self.assertEqual(result[c1.id], result[c3.id])
        
        # single cluster - every VM
        result = owner.used_resources(cluster=c1, only_running=False)
        self.assertEqual(result["disk"], 12)
        self.assertEqual(result["ram"], 2)
        self.assertEqual(result["virtual_cpus"], 6)
        
        # single cluster - only running VMs
        result = owner.used_resources(cluster=c1, only_running=True)
        self.assertEqual(result["disk"], 12)
        self.assertEqual(result["ram"], 1)
        self.assertEqual(result["virtual_cpus"], 3)
