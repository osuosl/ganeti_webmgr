from ganeti_web.tests.views.virtual_machine.base \
    import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineLogViews']


class TestVirtualMachineLogViews(TestVirtualMachineViewsBase):

    def test_view_object_log(self):
        """
        Tests view for object log:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/object_log/"
        args = (self.cluster.slug, self.vm.hostname)
        self.validate_get(url, args, 'object_log/log.html')
