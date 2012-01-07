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

global c
global cluster, vm
global user, users, group, vm_admin, vm_modify, cluster_migrate, \
    cluster_admin, superuser

class VirtualMachineTestCaseMixin():
    def create_virtual_machine(self, cluster=None, hostname='vm1.osuosl.bak'):
        cluster = cluster if cluster else Cluster(hostname='test.osuosl.bak', slug='OSL_TEST', username='foo', password='bar')
        cluster.save()
        cluster.sync_nodes()
        vm = VirtualMachine(cluster=cluster, hostname=hostname)
        vm.save()
        return vm, cluster


class TestVirtualMachineViewsBase(TestCase, VirtualMachineTestCaseMixin, ViewTestMixin, UserTestMixin):
    """
    Tests for views showing virtual machines
    """
    context=globals()

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        vm, cluster = self.create_virtual_machine()

        context = {}
        self.create_standard_users(context)
        self.create_users([
              ('user',{'id':69}),
              ('user1',{'id':88}),
              ('vm_admin',{'id':77}),
              ('vm_modify',{'id':75}),
              ('cluster_migrate',{'id':78}),
              ('cluster_admin',{'id':99}),
        ], context)
        globals().update(context)

        vm_admin.grant('admin', vm)
        vm_modify.grant('modify', vm)
        cluster_migrate.grant('migrate', cluster)
        cluster_admin.grant('admin', cluster)

        group = Group(id=42, name='testing_group')
        group.save()

        # XXX ensure namespaces for this module and child classes are updated
        context['c'] = Client()
        context['group'] = group
        context['vm'] = vm
        context['cluster'] = cluster
        context['cluster_admin'] = cluster_admin
        context['vm_admin'] = vm_admin
        globals().update(context)
        self.context.update(context)

    def tearDown(self):
        if vm is not None:
            vm.rapi.error = None

        VirtualMachineTemplate.objects.all().delete()
        Job.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Node.objects.all().delete()
        Cluster.objects.all().delete()

    def validate_get(self, url, args, template):
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, [superuser, vm_admin], template=template)

    def validate_get_configurable(self, url, args, template=None, mimetype=False, perms=None):
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
            user.set_perms(perms, vm)
        self.assert_200(url, args, [superuser, user], mime=mimetype, template=template)

    def validate_post_only_url(self, url, args=None, data=dict(), users=None,
                               get_allowed=False):
        """
        Generic function for POSTing to URLs.

        This function does some standard URL checks, then does two POSTs: One
        normal, and one with a faked error. Additionally, if ``get_allowed``
        is not set, the GET method is checked to make sure it fails.
        """

        vm = globals()['vm']
        args = args if args else (cluster.slug, vm.hostname)
        users = users if users else [superuser, vm_admin, cluster_admin]

        # Only do the standard assertions if GET is allowed. POST-only URLs
        # generally don't give a shit about any GET requests and will 405 all
        # of them.
        if get_allowed:
            self.assert_standard_fails(url, args)
        else:
            self.assertTrue(c.login(username=superuser.username, password='secret'))
            response = c.get(url % args, data)
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
            vm.rapi.error = None

        self.assert_200(url, args, users, data=data, tests=test_json,
                        mime='application/json', method='post')

        msg = "SIMULATING_AN_ERROR"
        vm.rapi.error = client.GanetiApiError(msg)
        self.assert_200(url, args, [superuser], data=data,
                        tests=test_json_error, mime='application/json',
                        method='post')
