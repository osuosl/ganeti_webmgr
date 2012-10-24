from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from ganeti_web.backend.queries import cluster_qs_for_user
from ganeti_web.models import Cluster

__all__ = (
    "TestClusterQSForUser",
)

class TestClusterQSForUser(TestCase):

    def test_cluster_qs_for_user_anon(self):
        user = AnonymousUser()
        qs = cluster_qs_for_user(user)
        self.assertFalse(qs)

    def test_cluster_qs_for_user_anon_empty(self):
        cluster = Cluster(hostname="example.org")
        cluster.save()

        user = AnonymousUser()
        qs = cluster_qs_for_user(user)
        self.assertNotIn(cluster, qs)

        cluster.delete()
