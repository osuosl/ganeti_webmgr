from ganeti.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineLogViews']

global cluster, vm

class TestVirtualMachineLogViews(TestVirtualMachineViewsBase):
    context = globals()

    def test_view_object_log(self):
        """
        Tests view for object log:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/object_log/"
        args = (cluster.slug, vm.hostname)
        self.validate_get(url, args, 'object_log/log.html')