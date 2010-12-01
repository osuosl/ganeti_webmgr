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


from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti.models import VirtualMachine, Cluster, ClusterUser, Profile, Organization

__all__ = ('TestClusterUser',)


class TestClusterUser(TestCase):
    
    def setUp(self):
        self.tearDown()
    
    def tearDown(self):
        User.objects.all().delete()
        ClusterUser.objects.all().delete()
        Organization.objects.all().delete()
        Group.objects.all().delete()
        Profile.objects.all().delete()
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
        self.assert_(profile, 'profile was not created')
        
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
        self.assert_(group.organization, 'profile was not created')
        
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
        
        self.assert_(isinstance(profile, (Profile,)))
    
    def test_casting_organization(self):
        """
        Tests casting ClusterUser into an Organization
        """
        group = Group(name='tester')
        group.save()
        
        cluster_user = ClusterUser.objects.all()[0]
        organization = cluster_user.cast()
        
        self.assert_(isinstance(organization, (Organization,)))
    
    def test_used_resources(self):
        """
        Tests retrieving dictionary of resources used by a cluster user
        """
        owner = ClusterUser(name='owner')
        owner.save()
        c = Cluster(hostname='testing')
        c.save()
        
        vm0 = VirtualMachine(hostname='one', owner=owner, cluster=c)
        vm1 = VirtualMachine(hostname='two', ram=1, virtual_cpus=3, disk_size=5, owner=owner, cluster=c)
        vm2 = VirtualMachine(hostname='three', ram=2, virtual_cpus=4, disk_size=6, owner=owner, cluster=c)
        vm3 = VirtualMachine(hostname='four', ram=3, virtual_cpus=5, disk_size=7, cluster=c)
        vm0.save()
        vm1.save()
        vm2.save()
        vm3.save()
        
        used = owner.used_resources
        self.assertEqual(1+2, used['ram'])
        self.assertEqual(3+4, used['virtual_cpus'])
        self.assertEqual(5+6, used['disk'])