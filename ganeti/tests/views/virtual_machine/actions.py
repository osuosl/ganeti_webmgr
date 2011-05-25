from ganeti.models import VirtualMachine, Job
from object_permissions import grant

from ganeti.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineActions']


global c, superuser, cluster_admin, cluster_migrate, user
global vm, cluster


class TestVirtualMachineActions(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_startup(self):
        """
        Test starting a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/startup')

    def test_view_startup_overquota(self):
        """
        Test starting a virtual machine that would cause the owner to exceed quota
        """
        vm = globals()['vm']
        args = (cluster.slug, vm.hostname)
        url = '/cluster/%s/%s/startup'

        # authorized (permission)
        self.assert_(c.login(username=user.username, password='secret'))

        grant(user, 'admin', vm)
        cluster.set_quota(user.get_profile(), dict(ram=10, disk=2000, virtual_cpus=10))
        vm.owner_id = user.get_profile().id
        vm.ram = 128
        vm.virtual_cpus = 1
        vm.save()

        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assert_('Owner does not have enough RAM' in response.content)
        user.revoke('admin', vm)
        VirtualMachine.objects.all().update(last_job=None)
        Job.objects.all().delete()

        # restore values
        cluster.set_quota(user.get_profile(), dict(ram=10, disk=2000, virtual_cpus=10))
        vm.owner_id = None
        vm.ram = -1
        vm.virtual_cpus = -1

    def test_view_shutdown(self):
        """
        Test shutting down a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/shutdown')

    def test_view_reboot(self):
        """
        Test rebooting a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/reboot')

    def test_view_migrate(self):
        """
        Tests migrating a virtual machine
        """
        url = '/cluster/%s/%s/migrate'
        args = (cluster.slug, vm.hostname)
        template='virtual_machine/migrate.html'
        authorized = [superuser, cluster_admin, cluster_migrate]

        # get
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, authorized, template=template)

        # post
        data = {'mode':'live'}
        self.validate_post_only_url(url, args, data, users=authorized, get_allowed=True)

