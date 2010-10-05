from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission


from ganeti.tests.rapi_proxy import RapiProxy, INFO
from ganeti import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Quota = models.Quota


__all__ = ('TestClusterViews', 'TestClusterModel')


class TestClusterModel(TestCase):
    
    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.tearDown()
    
    def tearDown(self):
        Cluster.objects.all().delete()
        User.objects.all().delete()
        Quota.objects.all().delete()

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
        self.assertEqual(user_quota, cluster.get_quota(user))
        
        # update quota with new values
        cluster.set_quota(user.get_profile(), user_quota2)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assertEqual(1, query.count())
        self.assertEqual(user_quota2, cluster.get_quota(user))
        
        # delete quota
        cluster.set_quota(user.get_profile(), None)
        query = Quota.objects.filter(cluster=cluster, user=user.get_profile())
        self.assertFalse(query.exists())
        self.assertEqual(default_quota, cluster.get_quota(user))
    
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
        self.assertFalse(VirtualMachine.objects.filter(cluster=cluster, hostname=vm_removed.hostname), 'vm not present in ganeti was not removed from db')

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
        
        self.cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        self.cluster.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('create', Cluster)

    def tearDown(self):
        Quota.objects.all().delete()
        ObjectPermission.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()

    def test_view_clusters(self):
        """
        Tests displaying the list of clusters
        """
        raise NotImplementedError
    
    def test_view_detail(self):
        """
        Tests displaying detailed view for a Cluster
        """
        raise NotImplementedError

    def test_view_users(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        user = self.user
        cluster = self.cluster
        c = Client()
        
        # anonymous user
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(403, response.status_code)
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/users/" % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        # authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/users.html')
        
        # authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get("/cluster/%s/users/" % cluster.slug)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/users.html')

    def test_view_user_permissions(self):
        """
        Tests updating users permissions
        
        Verifies:
            * anonymous user returns 403
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * missing user returns error as json
            * GET returns html for form
            * If user has permissions no html is returned
            * If user has no permissions a json response of -1 is returned
        """
        user = self.user
        user1 = self.user1
        cluster = self.cluster
        args = cluster.slug
        c = Client()
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get("/cluster/%s/user/" % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/user/?user=%s" % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get("/cluster/%s/user/" % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get("/cluster/%s/user/" % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # invalid user
        response = c.get("/cluster/%s/user/?user=%s" % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # valid POST user has permissions
        user1.grant('create', cluster)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post("/cluster/%s/user/" % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assert_(user1.has_perm('admin', cluster))
        self.assertFalse(user1.has_perm('create', cluster))
        
        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id}
        response = c.post("/cluster/%s/user/" % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(user, cluster))
        self.assertEqual('0', response.content)
        
        # valid POST user is new, but no permissions specified
        data = {'permissions':[], 'user':user1.id}
        response = c.post("/cluster/%s/user/" % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
    def test_view_user_quota(self):
        """
        Tests updating users quota
        
        Verifies:
            * anonymous user returns 403
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
        user = self.user
        user1 = self.user1
        profile = user1.get_profile()
        cluster = self.cluster
        cluster.__dict__.update(default_quota)
        cluster.save()
        args = (cluster.slug, user1.id)
        c = Client()
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get("/cluster/%s/user/quota/?user=%s" % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/user/quota/?user=%s" % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get("/cluster/%s/user/quota/?user=%s" % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get("/cluster/%s/user/quota/?user=%s" % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # invalid user
        response = c.get("/cluster/%s/user/quota/?user=%s" % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # no user
        response = c.get("/cluster/%s/user/quota/" % cluster.slug)
        self.assertEqual(404, response.status_code)
        
        # valid POST - setting unlimited values (nones)
        data = {'user':profile.id, 'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post("/cluster/%s/user/quota/" % cluster.slug, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(user1))
        query = Quota.objects.filter(cluster=cluster, user=user1.get_profile())
        self.assert_(query.exists())
        
        # valid POST - setting values
        data = {'user':profile.id, 'ram':4, 'virtual_cpus':5, 'disk':''}
        response = c.post("/cluster/%s/user/quota/" % cluster.slug, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_quota, cluster.get_quota(user1))
        self.assert_(query.exists())
        
        # valid POST - setting implicit unlimited (values are excluded)
        data = {'user':profile.id}
        response = c.post("/cluster/%s/user/quota/" % cluster.slug, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(user1))
        self.assert_(query.exists())
        
        # valid DELETE - returns to default values
        data = {'user':profile.id, 'delete':True}
        response = c.post("/cluster/%s/user/quota/" % cluster.slug, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual(default_quota, cluster.get_quota())
        self.assertFalse(query.exists())