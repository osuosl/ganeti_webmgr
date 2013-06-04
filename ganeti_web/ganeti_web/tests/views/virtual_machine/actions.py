from ganeti_web.models import VirtualMachine, Job
from object_permissions import grant

from ganeti_web.tests.views.virtual_machine.base \
    import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineActions']


class TestVirtualMachineActions(TestVirtualMachineViewsBase):

    def test_view_startup(self):
        """
        Test starting a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/startup')

    def test_view_startup_overquota(self):
        """
        Test starting a virtual machine that would cause the
        owner to exceed quota
        """
        args = (self.cluster.slug, self.vm.hostname)
        url = '/cluster/%s/%s/startup'

        # authorized (permission)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))

        grant(self.user, 'admin', self.vm)
        self.cluster.set_quota(self.user.get_profile(), dict(ram=10,
                                                             disk=2000,
                                                             virtual_cpus=10))
        self.vm.owner_id = self.user.get_profile().id
        self.vm.ram = 128
        self.vm.virtual_cpus = 1
        self.vm.save()

        response = self.c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertTrue('Owner does not have enough RAM' in response.content)
        self.user.revoke('admin', self.vm)
        VirtualMachine.objects.all().update(last_job=None)
        Job.objects.all().delete()

        # restore values
        # XXX wait, whoa, whoa, why do we need to do this?
        self.cluster.set_quota(self.user.get_profile(),
                               dict(ram=10, disk=2000, virtual_cpus=10))
        self.vm.owner_id = None
        self.vm.ram = -1
        self.vm.virtual_cpus = -1

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
        args = (self.cluster.slug, self.vm.hostname)
        template = 'ganeti/virtual_machine/migrate.html'
        authorized = [self.superuser, self.cluster_admin,
                      self.cluster_migrate]

        # get
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, authorized, template=template)

        # post
        data = {'mode': 'live'}
        self.validate_post_only_url(url, args, data, users=authorized,
                                    get_allowed=True)
