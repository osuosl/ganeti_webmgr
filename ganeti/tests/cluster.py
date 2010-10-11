from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import *
from object_permissions.models import ObjectPermissionType, ObjectPermission, \
    UserGroup, GroupObjectPermission


from ganeti.tests.rapi_proxy import RapiProxy, INFO, NODES, NODES_BULK
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
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()
        
        group = UserGroup(name='testing_group')
        group.save()
        
        cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        cluster.save()
        
        dict_ = globals()
        dict_['user'] = user
        dict_['user1'] = user1
        dict_['group'] = group
        dict_['cluster'] = cluster
        dict_['c'] = Client()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('create', Cluster)
        register('create_vm', Cluster)

    def tearDown(self):
        Quota.objects.all().delete()
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        Cluster.objects.all().delete()
        UserGroup.objects.all().delete()
        User.objects.all().delete()

    def validate_get(self, url, args, template):
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        # authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)

    def test_view_list(self):
        """
        Tests displaying the list of clusters
        """
        url = '/clusters/'
        
        # create extra user and tests
        user2 = User(id=4, username='tester2', is_superuser=True)
        user2.set_password('secret')
        user2.save()
        cluster1 = Cluster(hostname='cluster1', slug='cluster1')
        cluster2 = Cluster(hostname='cluster2', slug='cluster2')
        cluster3 = Cluster(hostname='cluster3', slug='cluster3')
        cluster1.save()
        cluster2.save()
        cluster3.save()
        
        # grant some perms
        user1.grant('admin', cluster)
        user1.grant('create_vm', cluster1)
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assertFalse(clusters)
        
        # authorized permissions
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 in clusters)
        self.assertEqual(2, len(clusters))
        
        # authorized (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/list.html')
        clusters = response.context['cluster_list']
        self.assert_(cluster in clusters)
        self.assert_(cluster1 in clusters)
        self.assert_(cluster2 in clusters)
        self.assert_(cluster3 in clusters)
        self.assertEqual(4, len(clusters))
    
    def test_view_detail(self):
        """
        Tests displaying detailed view for a Cluster
        """
        url = '/cluster/%s/'
        args = cluster.slug
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/detail.html')

    def test_view_users(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/users/"
        args = cluster.slug
        self.validate_get(url, args, 'cluster/users.html')

    def test_view_virtual_machines(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/virtual_machines/"
        args = cluster.slug
        self.validate_get(url, args, 'virtual_machine/table.html')

    def test_view_nodes(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent cluster returns 404
        """
        url = "/cluster/%s/nodes/"
        args = cluster.slug
        cluster.rapi.GetNodes.response = NODES_BULK
        self.validate_get(url, args, 'node/table.html')
        cluster.rapi.GetNodes.response = NODES

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or UserGroup
        """
        url = '/cluster/%s/permissions/'
        args = cluster.slug
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % "DOES_NOT_EXIST")
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # no user or group
        data = {'permissions':['admin']}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # both user and group
        data = {'permissions':['admin'], 'group':group.id, 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - user
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - group
        data = {'permissions':[], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST user has permissions
        user1.grant('create', cluster)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assert_(user1.has_perm('admin', cluster))
        self.assertFalse(user1.has_perm('create', cluster))
        
        # valid POST group has permissions
        group.grant('create', cluster)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(['admin'], group.get_perms(cluster))

    def test_view_user_permissions(self):
        """
        Tests updating users permissions
        
        Verifies:
            * anonymous user returns 403
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * invalid group returns 404
            * missing user and group returns error as json
            * GET returns html for form
            * If user/group has permissions no html is returned
            * If user/group has no permissions a json response of -1 is returned
        """
        args = (cluster.slug, user1.id)
        args_post = cluster.slug
        url = "/cluster/%s/permissions/user/%s"
        url_post = "/cluster/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, -1))
        self.assertEqual(404, response.status_code)
        
        # invalid user (POST)
        user1.grant('create', cluster)
        data = {'permissions':['admin'], 'user':-1}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no user (POST)
        user1.grant('create', cluster)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST user has permissions
        user1.grant('create', cluster)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assert_(user1.has_perm('admin', cluster))
        self.assertFalse(user1.has_perm('create', cluster))
        
        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(user, cluster))
        self.assertEqual('0', response.content)

    def test_view_group_permissions(self):
        """
        Test editing UserGroup permissions on a Cluster
        """
        args = (cluster.slug, group.id)
        args_post = cluster.slug
        url = "/cluster/%s/permissions/group/%s"
        url_post = "/cluster/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/permissions.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/permissions.html')        
        
        # invalid group
        response = c.get(url % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # invalid group (POST)
        data = {'permissions':['admin'], 'group':-1}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no group (POST)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST group has permissions
        group.grant('create', cluster)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(['admin'], group.get_perms(cluster))
        
        # valid POST group has no permissions left
        data = {'permissions':[], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], group.get_perms(cluster))
        self.assertEqual('0', response.content)
        
    def test_view_user_quota(self):
        """
        Tests updating users quota
        
        Verifies:
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
        cluster.__dict__.update(default_quota)
        cluster.save()
        cluster_user = user1.get_profile()
        args = (cluster.slug, cluster_user.id)
        args_post = cluster.slug
        url = '/cluster/%s/quota/%s'
        url_post = '/cluster/%s/quota/'
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/user/quota/?user=%s" % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # no user (GET)
        response = c.get(url_post % args_post)
        self.assertEqual(404, response.status_code)
        
        # no user (POST)
        data = {'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST - setting unlimited values (nones)
        data = {'user':cluster_user.id, 'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        query = Quota.objects.filter(cluster=cluster, user=cluster_user)
        self.assert_(query.exists())
        
        # valid POST - setting values
        data = {'user':cluster_user.id, 'ram':4, 'virtual_cpus':5, 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_quota, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid POST - setting implicit unlimited (values are excluded)
        data = {'user':cluster_user.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid DELETE - returns to default values
        data = {'user':cluster_user.id, 'delete':True}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/user_row.html')
        self.assertEqual(default_quota, cluster.get_quota(cluster_user))
        self.assertFalse(query.exists())
    
    def test_view_group_quota(self):
        """
        Tests updating a UserGroups quota
        
        Verifies:
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
        cluster.__dict__.update(default_quota)
        cluster.save()
        cluster_user = group.organization
        args = (cluster.slug, cluster_user.id)
        args_post = cluster.slug
        url = '/cluster/%s/quota/%s'
        url_post = '/cluster/%s/quota/'
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get("/cluster/%s/user/quota/?user=%s" % ("DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # valid GET authorized user (superuser)
        user.revoke('admin', cluster)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/quota.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, 0))
        self.assertEqual(404, response.status_code)
        
        # no user (GET)
        response = c.get(url_post % args_post)
        self.assertEqual(404, response.status_code)
        
        # no user (POST)
        data = {'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST - setting unlimited values (nones)
        data = {'user':cluster_user.id, 'ram':'', 'virtual_cpus':'', 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        query = Quota.objects.filter(cluster=cluster, user=cluster_user)
        self.assert_(query.exists())
        
        # valid POST - setting values
        data = {'user':cluster_user.id, 'ram':4, 'virtual_cpus':5, 'disk':''}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(user_quota, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid POST - setting implicit unlimited (values are excluded)
        data = {'user':cluster_user.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(user_unlimited, cluster.get_quota(cluster_user))
        self.assert_(query.exists())
        
        # valid DELETE - returns to default values
        data = {'user':cluster_user.id, 'delete':True}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cluster/group_row.html')
        self.assertEqual(default_quota, cluster.get_quota())
        self.assertFalse(query.exists())