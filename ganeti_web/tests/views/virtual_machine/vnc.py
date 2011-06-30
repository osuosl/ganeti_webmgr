from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineVNCViews']

global cluster, vm

class TestVirtualMachineVNCViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_vnc(self):
        """
        Tests view for cluster Ajax vnc (noVNC) script:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/vnc/"
        args = (cluster.slug, vm.hostname)
        self.validate_get(url, args, 'ganeti/virtual_machine/novnc.html')

    def test_view_vnc_proxy(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
            * no ports set (not running proxy)
        """
        url = "/cluster/%s/%s/vnc_proxy/"
        args = (cluster.slug, vm.hostname)
        self.validate_get_configurable(url, args, None, "application/json",
            ["admin",])