from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineVNCViews']

class TestVirtualMachineVNCViews(TestVirtualMachineViewsBase):

    def test_view_vnc(self):
        pass
        """
        Tests view for cluster Ajax vnc (noVNC) script:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """

        url = "/cluster/%s/%s/vnc/"
        args = (self.cluster.slug, self.vm.hostname)
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
        args = (self.cluster.slug, self.vm.hostname)

        self.assert_standard_fails(url, args, method="post")
        self.assert_200(url, 
                        args, 
                        [self.superuser, self.cluster_admin, self.vm_admin], 
                        method="post",
                        mime="application/json")
