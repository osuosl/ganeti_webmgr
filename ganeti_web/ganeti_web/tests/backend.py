from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

from django_test_tools.users import UserTestMixin

from ..backend.queries import cluster_qs_for_user, owner_qs_for_cluster
from clusters.models import Cluster

__all__ = (
    "TestClusterQSForUser",
    "TestOwnerQSForCluster",
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


class TestOwnerQSForCluster(TestCase):

    def test_owner_qs_for_cluster_none(self):
        qs = owner_qs_for_cluster(None)
        self.assertFalse(qs)
