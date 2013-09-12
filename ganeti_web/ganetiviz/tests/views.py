from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django.utils import unittest, simplejson as json

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from clusters.models import Cluster
from nodes.models import Node
from virtualmachines.models import VirtualMachine

__all__ = ['TestGanetivizViews', ]

testcluster0_data = {'nodes': [{'hostname': 'node0.example.test',
            'offline': False,
            'ram_free': -1,
            'ram_total': -1,
            'role': u''},
           {'hostname': 'node1.example.test',
            'offline': False,
            'ram_free': -1,
            'ram_total': -1,
            'role': u''}],
 'vms': [{'hostname': 'instance1.example.test',
          'owner': None,
          'primary_node__hostname': 'node0.example.test',
          'secondary_node__hostname': 'node1.example.test',
          'status': u''},
         {'hostname': 'instance2.example.test',
          'owner': None,
          'primary_node__hostname': 'node0.example.test',
          'secondary_node__hostname': 'node1.example.test',
          'status': u''},
         {'hostname': 'instance3.example.test',
          'owner': None,
          'primary_node__hostname': 'node0.example.test',
          'secondary_node__hostname': 'node1.example.test',
          'status': u''},
         {'hostname': 'instance4.example.test',
          'owner': None,
          'primary_node__hostname': 'node1.example.test',
          'secondary_node__hostname': 'node0.example.test',
          'status': u''}]}

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
        node_list.append(Node(cluster=cluster, hostname='node0.example.test',
                              offline=False))
        node_list.append(Node(cluster=cluster, hostname='node1.example.test',
                              offline=False))
        for node in node_list:
            node.save()

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
        for instance in instance_list:
            instance.save()

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

    def test_cluster_json_ouput(self):
        url = "/ganetiviz/cluster/%s/"
        args = self.cluster.slug

        self.c.login(username='tester_pranjal', password='secret')
        response = self.c.get(url % args)
        content = response.content
        cluster_data = json.loads(content)

        self.assertEqual(cluster_data,testcluster0_data)

