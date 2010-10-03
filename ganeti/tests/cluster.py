from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission


from ganeti.tests.rapi_proxy import RapiProxy
from ganeti import models
Cluster = models.Cluster

__all__ = ('TestClusterViews', 'TestClusterModel')


class TestClusterModel(TestCase):
    
    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.tearDown()
    
    def tearDown(self):
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
        
        cluster = Cluster(hostname='foo.fake.hostname')
        cluster.save()
        self.assert_(cluster.hash)
    
    def test_load_info(self):
        """
        Test loading remote info from ganeti cluster
        """
        pass
    
    def test_load_info_failed(self):
        """
        Test creating a cluster that cannot connect to the cluster to retrieve
        remote info
        """
        pass


class TestClusterViews(TestCase):
    
    def setUp(self):
        self.tearDown()
        
        User(id=1, username='anonymous').save()
        settings.ANONYMOUS_USER_ID=1
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()
        
        self.cluster = Cluster()
        self.cluster.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)

    def tearDown(self):
        Cluster.objects.all().delete()
        User.objects.all().delete()
        ObjectPermission.objects.all().delete()

    def test_trivial(self):
        pass

    def test_view_users(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        cluster = self.cluster
        c = Client()
        
        # no permissions
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/users/" % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(200, response.status_code)

    def test_view_user_permissions(self):
        pass
    
    