from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
# Per #6579, do not change this import without discussion.
from django.utils import simplejson as json

from django_test_tools.views import ViewTestMixin
from django_test_tools.users import UserTestMixin
from ganeti_web.models import VirtualMachineTemplate

from ganeti_web.util import client
from ganeti_web.tests.rapi_proxy import RapiProxy
from ganeti_web import models

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
Node = models.Node
Job = models.Job

class VirtualMachineTestCaseMixin():
    def create_virtual_machine(self, cluster=None, hostname='vm1.osuosl.bak'):
        cluster = cluster if cluster else Cluster(hostname='test.osuosl.bak',
                                                  slug='OSL_TEST',
                                                  username='foo',
                                                  password='bar')
        cluster.save()
        cluster.sync_nodes()
        vm = VirtualMachine(cluster=cluster, hostname=hostname)
        vm.save()
        return vm, cluster


class TestVirtualMachineViewsBase(TestCase, VirtualMachineTestCaseMixin,
                                  ViewTestMixin, UserTestMixin):
    """
    Tests for views showing virtual machines
    """

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.vm, self.cluster = self.create_virtual_machine()

        self.create_standard_users()
        self.create_users([
              ('user',{'id':69}),
              ('user1',{'id':88}),
              ('vm_admin',{'id':77}),
              ('vm_modify',{'id':75}),
              ('cluster_migrate',{'id':78}),
              ('cluster_admin',{'id':99}),
        ])

        self.vm_admin.grant('admin', self.vm)
        self.vm_modify.grant('modify', self.vm)
        self.cluster_migrate.grant('migrate', self.cluster)
        self.cluster_admin.grant('admin', self.cluster)

        self.group = Group(id=42, name='testing_group')
        self.group.save()

        self.c = Client()

    def tearDown(self):
        if self.vm is not None:
            self.vm.rapi.error = None

        VirtualMachineTemplate.objects.all().delete()
        Job.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()

    def validate_get(self, url, args, template):
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, [self.superuser, self.vm_admin],
                        template=template)

    def validate_get_configurable(self, url, args, template=None,
                                  mimetype=False, perms=None):
        """
        More configurable version of validate_get.
        Additional arguments (only if set) affects only authorized user test.

        @template: used template
        @mimetype: returned mimetype
        @perms:    set of perms granted on authorized user

        @return    response content
        """
        perms = [] if perms is None else perms

        self.assert_standard_fails(url, args)

        # authorized user (perm)
        if perms:
            self.user.set_perms(perms, self.vm)
        self.assert_200(url, args, [self.superuser, self.user], mime=mimetype,
                        template=template)

    def validate_post_only_url(self, url, args=None, data=dict(), users=None,
                               get_allowed=False):
        """
        Generic function for POSTing to URLs.

        This function does some standard URL checks, then does two POSTs: One
        normal, and one with a faked error. Additionally, if ``get_allowed``
        is not set, the GET method is checked to make sure it fails.
        """

        args = args if args else (self.cluster.slug, self.vm.hostname)
        users = users if users else [self.superuser, self.vm_admin,
                                     self.cluster_admin]

        # Only do the standard assertions if GET is allowed. POST-only URLs
        # generally don't give a shit about any GET requests and will 405 all
        # of them.
        if get_allowed:
            self.assert_standard_fails(url, args)
        else:
            self.assertTrue(self.c.login(username=self.superuser.username,
                                         password='secret'))
            response = self.c.get(url % args, data)
            self.assertEqual(405, response.status_code)

        def test_json(user, response):
            content = json.loads(response.content)
            self.assertEqual('1', content['id'])
            VirtualMachine.objects.all().update(last_job=None)
            Job.objects.all().delete()

        def test_json_error(user, response):
            content = json.loads(response.content)
            text = content['__all__'][0]
            self.assertEqual(msg, text)
            self.vm.rapi.error = None

        self.assert_200(url, args, users, data=data, tests=test_json,
                        mime='application/json', method='post')

        msg = "SIMULATING_AN_ERROR"
        self.vm.rapi.error = client.GanetiApiError(msg)
        self.assert_200(url, args, [self.superuser], data=data,
                        tests=test_json_error, mime='application/json',
                        method='post')
