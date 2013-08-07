from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import TestCase

from django_test_tools.users import UserTestMixin

from ganeti_web.backend.queries import cluster_qs_for_user, owner_qs
from ganeti_web.models import Cluster

__all__ = (
    "TestClusterQSForUser",
    "TestOwnerQSNoGroups",
    "TestOwnerQSGroups",
)


class TestClusterQSForUser(TestCase, UserTestMixin):

    def setUp(self):
        self.users = self.create_standard_users()
        # Non read-only cluster
        self.cluster = Cluster.objects.create(
            hostname="cluster1.example.org", slug="cluster1",
            username='foo', password='bar', mtime=1)

    def tearDown(self):
        # Tear down users
        for user in self.users.values():
            user.delete()
        # Tear down cluster
        self.cluster.delete()

    def test_cluster_qs_for_user_anon(self):
        user = AnonymousUser()
        qs = cluster_qs_for_user(user)
        self.assertFalse(qs)

    def test_cluster_qs_for_superuser(self):
        user = self.superuser
        qs = cluster_qs_for_user(user)
        self.assertQuerysetEqual(qs, [repr(self.cluster)], ordered=False)

    def test_cluster_qs_on_readonly_cluster(self):
        """
        Read only clusters should not be returned when using
        cluster_qs_for_user unless you pass readonly=True as a kwarg.
        """
        user = self.superuser
        # create a read only cluster (no username)
        ro_cluster = Cluster.objects.create(hostname="foo.example.org",
                                            slug="foo")
        qs = cluster_qs_for_user(user, readonly=False)
        self.assertNotIn(ro_cluster, qs)
        qs = cluster_qs_for_user(user, readonly=True)
        expected_clusters = [repr(self.cluster), repr(ro_cluster)]
        self.assertQuerysetEqual(qs, expected_clusters, ordered=False)
        # Cleanup
        ro_cluster.delete()

    def test_cluster_qs_user_with_userperms(self):
        user = self.create_user('cluster_admin')
        user.grant('admin', self.cluster)
        qs = cluster_qs_for_user(user)
        self.assertQuerysetEqual(qs, [repr(self.cluster)])

        user.delete()

    def test_cluster_qs_for_user_with_groupperms(self):
        group = Group.objects.create(name='cluster_admin')
        user = self.create_user('user')

        group.grant('admin', self.cluster)
        group.user_set.add(user)

        qs = cluster_qs_for_user(user)
        self.assertQuerysetEqual(qs, [repr(self.cluster)])

        user.delete()
        group.delete()

    def test_cluster_qs_user_without_perms(self):
        user = self.create_user('cluster_admin')
        qs = cluster_qs_for_user(user)
        self.assertFalse(qs)

        user.delete()


class TestOwnerQSNoGroups(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser('super', None, 'secret')
        self.admin = User.objects.create_user('admin', password='secret')
        self.noperms = User.objects.create_user('noperms', password='secret')

        self.cluster = Cluster.objects.create(
            hostname="cluster1.example.org", slug="cluster1",
            username='foo', password='bar', mtime=1)

        self.admin.grant('admin', self.cluster)

    def tearDown(self):
        self.superuser.delete()
        self.admin.delete()
        self.noperms.delete()

        self.cluster.delete()

    def test_no_cluster(self):
        owners = owner_qs(None, self.admin)
        self.assertQuerysetEqual(owners, [])

    def test_superuser(self):
        owners = owner_qs(self.cluster, self.superuser)
        valid_owners_list = [self.admin, self.noperms, self.superuser]
        valid_owners = map(lambda user: user.get_profile(), valid_owners_list)
        self.assertQuerysetEqual(owners, map(repr, valid_owners))

    def test_admin_user(self):
        owners = owner_qs(self.cluster, self.admin)
        valid_owners = [self.admin.get_profile()]
        self.assertQuerysetEqual(owners, map(repr, valid_owners))

    def test_noperms_user(self):
        owners = owner_qs(self.cluster, self.noperms)
        self.assertQuerysetEqual(owners, [])

    def test_create_vm_perms(self):
        self.noperms.grant('create_vm', self.cluster)
        owners = owner_qs(self.cluster, self.noperms)
        valid_owners = [repr(self.noperms.get_profile())]
        self.assertQuerysetEqual(owners, valid_owners)

class TestOwnerQSGroups(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_superuser('super', None, 'secret')
        self.standard = User.objects.create_user('standard', password='secret')

        self.admin_group = Group.objects.create(name='admin_group')
        self.non_admin_group = Group.objects.create(name='non_admin_group')

        self.standard.groups = [self.admin_group, self.non_admin_group]

        self.cluster = Cluster.objects.create(
            hostname="cluster1.example.org", slug="cluster1",
            username='foo', password='bar', mtime=1)

        self.admin_group.grant('admin', self.cluster)

    def tearDown(self):
        self.superuser.delete()
        self.standard.delete()

        self.admin_group.delete()
        self.non_admin_group.delete()

        self.cluster.delete()

    def test_superuser(self):
        owners = owner_qs(self.cluster, self.superuser)
        valid_owners = [self.admin_group.organization,
                        self.non_admin_group.organization,
                        self.standard.get_profile(),
                        self.superuser.get_profile()]

        self.assertQuerysetEqual(owners, map(repr, valid_owners))

    def test_user_in_admin_group(self):
        owners = owner_qs(self.cluster, self.standard)
        valid_owners = [repr(self.admin_group.organization)]
        self.assertQuerysetEqual(owners, valid_owners)

    def test_user_in_non_admin_group(self):
        self.standard.groups.remove(self.admin_group)
        owners = owner_qs(self.cluster, self.standard)
        self.assertQuerysetEqual(owners, [])

    def test_create_vm_perms_group(self):
        self.non_admin_group.grant('create_vm', self.cluster)
        owners = owner_qs(self.cluster, self.standard)
        valid_owners = [self.admin_group.organization,
                        self.non_admin_group.organization]
        self.assertQuerysetEqual(owners, map(repr, valid_owners))
