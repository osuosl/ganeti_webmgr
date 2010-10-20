from django.contrib.auth.models import User
from django.test import TestCase

from object_permissions.models import UserGroup

from ganeti.models import VirtualMachine, Cluster, ClusterUser, Profile, Organization

__all__ = ('TestClusterUser',)


class TestClusterUser(TestCase):
    
    def setUp(self):
        self.tearDown()
    
    def tearDown(self):
        User.objects.all().delete()
        ClusterUser.objects.all().delete()
        Organization.objects.all().delete()
        UserGroup.objects.all().delete()
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
    
    def test_user_group_signal(self):
        """
        Test signals related to User:
        
        Verifies:
            * organization is created/deleted with UserGroup
        """
        group = UserGroup(name='tester')
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
        group = UserGroup(name='tester')
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