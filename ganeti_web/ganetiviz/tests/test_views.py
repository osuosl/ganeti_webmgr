from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django.test import LiveServerTestCase
from django.utils import unittest, simplejson as json

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from clusters.models import Cluster
from nodes.models import Node
from virtualmachines.models import VirtualMachine

try:
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    SELENIUM_NOT_INSTALLED = False
except ImportError:
    SELENIUM_NOT_INSTALLED = True


class TestGanetivizViews(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='tester_pranjal',password='secret')
        group = Group(name='testing_group')
        group.save()

        # Creating Test Cluster
        ## Creating Test Cluster
        cluster = Cluster.objects.create(hostname='cluster0.example.test',
                          slug='cluster0')

        # Creating Test nodes for the cluster.
        node_list = []
        node_list.append(Node.objects.create(cluster=cluster, 
                         hostname='node0.example.test',offline=False))
        node_list.append(Node.objects.create(cluster=cluster, 
                         hostname='node1.example.test',offline=False))

        # Creating Test instances for the cluster.
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance1.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance2.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance3.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance4.example.test',
                                      primary_node=node_list[1],
                                      secondary_node=node_list[0])

        self.user = user
        self.group = group
        self.cluster = cluster

    def tearDown(self):
        # Tear down users.
        self.user.delete()
        self.group.delete()

        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()

    def test_cluster_json_ouput(self):
        testcluster0_data = {
        'nodes': [{'hostname': 'node0.example.test',
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

        url = "/ganetiviz/cluster/%s/"
        args = self.cluster.slug

        self.client.login(username='tester_pranjal', password='secret')
        response = self.client.get(url % args)
        content = response.content
        cluster_data = json.loads(content)

        self.assertEqual(cluster_data,testcluster0_data)



def check_help_status(driver):
    help_status = driver.execute_script("return window.GANETIVIZ_HELP_MODE")
    return help_status

# Selenium tests use Django LiveServer for testing. LiveServer runs on port 8081 in the background
@unittest.skipIf(SELENIUM_NOT_INSTALLED,"Skipping selenium tests, as selenium is not installed")
class GanetivizSeleniumTests(LiveServerTestCase):
    def setUp(self):
        super(GanetivizSeleniumTests, self).setUp()
        self.driver = webdriver.Firefox()

        # Loading initial data.
        user = User.objects.create_user(username='tester_pranjal',password='secret')

        group = Group(name='testing_group')
        group.save()

        ## Creating Test Cluster
        cluster = Cluster.objects.create(hostname='cluster0.example.test',
                          slug='cluster0')

        # Creating Test nodes for the cluster.
        node_list = []
        node_list.append(Node.objects.create(cluster=cluster, 
                         hostname='node0.example.test',offline=False))
        node_list.append(Node.objects.create(cluster=cluster, 
                         hostname='node1.example.test',offline=False))

        ## Creating Test instances for the cluster.
        # Creating Test instances for the cluster.
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance1.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance2.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance3.example.test',
                                      primary_node=node_list[0],
                                      secondary_node=node_list[1])
        VirtualMachine.objects.create(cluster=cluster,
                                      hostname='instance4.example.test',
                                      primary_node=node_list[1],
                                      secondary_node=node_list[0])

        self.user = user
        self.group = group
        self.cluster = cluster

    def tearDown(self):
        self.driver.quit()
        super(GanetivizSeleniumTests, self).tearDown()

    def test_user_interface(self):
        #self.c.login(username='tester_pranjal', password='secret')
        driver = self.driver
        driver.get("http://localhost:8081/map/cluster0/")

        if driver.title == u'Login':
            element = driver.find_element_by_id("id_username")
            element.send_keys("tester_pranjal")
            element = driver.find_element_by_id("id_password")
            element.send_keys("secret")
            element.send_keys(Keys.ENTER)
            driver.get("http://localhost:8000/map/cluster0/")

        html_document = driver.find_element_by_xpath("/html")
        helpdiv = driver.find_element_by_id("help-div")

        # Checking if title is Ok.
        assert "Ganeti Cluster Mapping" in driver.title

        # Checking if help appears on clicking on a help-div
        helpdiv.click();
        assert check_help_status(driver) == True

        # Checking if help toggles back to off on clicking on help-div.
        helpdiv.click();
        assert check_help_status(driver) == False

        # Checking if pressing the 'h' key opens the help
        html_document.send_keys('h')
        assert check_help_status(driver) == True

        # Checking if panning works fine.
        html_document.send_keys(Keys.ARROW_LEFT)
        html_document.send_keys(Keys.ARROW_LEFT)
        html_document.send_keys(Keys.ARROW_RIGHT)
        html_document.send_keys(Keys.ARROW_RIGHT)
        html_document.send_keys(Keys.ARROW_UP)
        html_document.send_keys(Keys.ARROW_UP)
        html_document.send_keys(Keys.ARROW_DOWN)
        html_document.send_keys(Keys.ARROW_DOWN)
        # Question - How to assert whether the check works fine.

        # Todo: Looking for an answer to-
        # http://stackoverflow.com/questions/18436248/writing-selenium-tests-for-cytoscape-js-applications-locating-nodes-edges

