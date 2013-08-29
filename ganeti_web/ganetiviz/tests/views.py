from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from object_permissions import get_user_perms

from utils.proxy.constants import NODES, NODES_BULK

from ganeti_web.models import Cluster, Node, VirtualMachine
from ganeti_web.views.generic import LoginRequiredMixin
from utils.models import Quota, SSHKey

from ganeti_web.models import Cluster, Node, VirtualMachine

__all__ = ['TestGanetivizViews',]


class TestGanetivizViews(TestCase, ViewTestMixin, UserTestMixin):
    def setUp(self):
        user = User(id=2, username='tester_pranjal')
        user.set_password('secret')
        user.save()

        group = Group(name='testing_group')
        group.save()

        # Creating Test Cluster
        cluster = Cluster(hostname='cluster0.example.test',
                                    slug='cluster0')
        cluster.save()

        self.create_standard_users()
        self.create_users(['cluster_admin'])
        self.cluster_admin.grant('admin', cluster)

        # Creating Test nodes for the cluster.
        node_list = []
        node_list.append(Node(cluster=cluster,hostname='node0.example.test',offline=False))
        node_list.append(Node(cluster=cluster,hostname='node1.example.test',offline=False))

        # Creating Test instances for the cluster.
        instance_list = []
        instance_list.append(VirtualMachine(cluster=cluster,
                                            hostname='instance1.example.test',
                                            primary_node=node_list[0],
                                            secondary_node=node_list[1]))
        instance_list.append(VirtualMachine(cluster=cluster,
                                            hostname='instance2.example.test',
                                            primary_node=node_list[0],
                                            secondary_node=node_list[1]))
        instance_list.append(VirtualMachine(cluster=cluster,
                                            hostname='instance3.example.test',
                                            primary_node=node_list[0],
                                            secondary_node=node_list[1]))
        instance_list.append(VirtualMachine(cluster=cluster,
                                            hostname='instance4.example.test',
                                            primary_node=node_list[1],
                                            secondary_node=node_list[0]))

        self.user = user
        self.group = group
        self.cluster = cluster
        self.c = Client()


    def tearDown(self):
        # Tear down users.
        self.user.delete()
        self.unauthorized.delete()
        self.superuser.delete()
        self.cluster_admin.delete()

        self.group.delete()

        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()

    def testJsonOuput(self):
        #TODO
        response = self.c.get('/ganetiviz/vms/cluster0')
        content = response.content
        print content
        #self.assertEqual(1, 1, "One did not equal 1")
