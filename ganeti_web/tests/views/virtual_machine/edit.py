from django.contrib.auth.models import User
from django.utils import simplejson as json

from ganeti_web import models
from ganeti_web.tests.rapi_proxy import JOB_RUNNING
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase
from ganeti_web.utilities import cluster_os_list

__all__ = ['TestVirtualMachineEditViews',
           'TestVirtualMachineDeleteViews',
           'TestVirtualMachineReinstallViews',
           'TestVirtualMachineRenameViews',
           'TestVirtualMachineReparentViews']

VirtualMachine = models.VirtualMachine


class TestVirtualMachineEditViews(TestVirtualMachineViewsBase):

    def test_view_modify(self):
        """
        Test modifying an instance
        """

        args = (self.cluster.slug, self.vm.hostname)
        url = '/cluster/%s/%s/edit' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()

        ## GET
        # Anonymous User
        response = self.c.get(url)
        self.assertEqual(302, response.status_code)

        # User with Modify Permissions
        user.grant('modify', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm('modify', self.vm))
        self.assertFalse(user.has_perm('admin', self.vm))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(self.vm)
        self.c.logout()

        # User with Admin Permissions
        user.grant('admin', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(self.vm)
        self.c.logout()

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        self.c.logout()
        user.is_superuser = False
        user.save()

        ## POST
        os_list = cluster_os_list(self.cluster)
        data = dict(vcpus=2,
            acpi=True,
            disk_cache='default',
            initrd_path='',
            kernel_args='ro',
            kvm_flag='',
            mem_path='',
            migration_downtime=30,
            security_domain='',
            security_model='none',
            usb_mouse='',
            use_chroot=False,
            use_localtime=False,
            vnc_bind_address='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_count_original=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='',
            cdrom2_image_path='')

        # Required Values
        user.grant('modify', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        for property in ['vcpus', 'memory', 'disk_type', 'boot_order',
                         'nic_type']:
            data_ = data.copy()
            del data_[property]
            self.assertFalse(user.is_superuser)
            response = self.c.post(url, data_)
            # If failure then a field that is not required by the model, but
            #  should be required by the form, is not being required by
            #  the form. See the ModifyVirtualMachineForm.required field.
            self.assertNotEqual(response.context['form'][property].errors, [], msg=property)
            self.assertEqual(200, response.status_code) # 302 if success (BAD)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        self.c.logout()
        user.revoke_all(self.vm)


        # Anonymous User
        response = self.c.post(url, data)
        self.assertEqual(302, response.status_code)

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertTrue(user.is_superuser)
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.c.logout()
        user.is_superuser = False
        user.save()

        # User without Permissions
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(403, response.status_code)
        self.assertTrue(response.context['message'])
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, '403.html')
        self.c.logout()

        # User with Modify Permissions
        user.grant('modify', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        user.revoke_all(self.vm)
        self.c.logout()

        # User with Admin Permissions
        user.grant('admin', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        user.revoke_all(self.vm)
        self.c.logout()

    def test_view_modify_confirm(self):
        """
        Test confirm page for modifying an instance
        """

        args = (self.cluster.slug, self.vm.hostname)
        url = '/cluster/%s/%s/edit/confirm' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()

        self.vm.owner = user.get_profile()
        self.vm.save()

        os_list = cluster_os_list(self.cluster)
        edit_form = dict(vcpus=2,
            acpi=True,
            disk_cache='default',
            initrd_path='',
            kernel_args='ro',
            kvm_flag='',
            mem_path='',
            migration_downtime=30,
            security_domain='',
            security_model='none',
            usb_mouse='',
            use_chroot=False,
            use_localtime=False,
            vnc_bind_address='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_count_original=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')

        ## SESSION VARIABLES
        # Make sure session variables are set
        user.is_superuser = True
        user.save()
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        # edit_form
        response = self.c.get(url)
        self.assertEqual(400, response.status_code)
        session['edit_form'] = edit_form
        session.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')

        #session['os_list'] = os_list
        #session.save()
        user.revoke_all(self.vm)
        user.is_superuser = False
        user.save()
        self.c.logout()

        ## GET
        # Anonymous User
        response = self.c.get(url)
        self.assertEqual(302, response.status_code)

        # User with Modify Permissions
        user.grant('modify', self.vm)
        self.assertFalse(user.is_superuser)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        user.revoke_all(self.vm)
        self.c.logout()

        # User with Admin Permissions
        user.grant('admin', self.vm)
        self.assertFalse(user.is_superuser)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        user.revoke_all(self.vm)
        self.c.logout()

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        self.c.logout()
        user.is_superuser = False
        user.save()

        ## POST
        data = {'rapi_dict':json.dumps(edit_form)}
        # Anonymous User
        response = self.c.post(url, data)
        self.assertEqual(302, response.status_code)

        for i in ('cancel', 'edit', 'save', 'reboot'):
            data[i] = True

            # Superuser
            user.is_superuser = True
            user.save()
            self.assertTrue(self.c.login(username=user.username,
                                         password='secret2'))
            session = self.c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertTrue(user.is_superuser)
            response = self.c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.c.logout()
            user.is_superuser = False
            user.save()

            # User without Permissions
            self.assertTrue(self.c.login(username=user.username,
                                         password='secret2'))
            self.assertFalse(user.is_superuser)
            response = self.c.post(url, data)
            self.assertEqual(403, response.status_code)
            self.assertTrue(response.context['message'])
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, '403.html')
            self.c.logout()

            # User with Modify Permissions
            user.grant('modify', self.vm)
            user.grant('power', self.vm)
            self.assertTrue(self.c.login(username=user.username,
                                         password='secret2'))
            session = self.c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertFalse(user.is_superuser)
            response = self.c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            user.revoke_all(self.vm)
            self.c.logout()

            # User with Admin Permissions
            user.grant('admin', self.vm)
            self.assertTrue(self.c.login(username=user.username,
                                         password='secret2'))
            session = self.c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertFalse(user.is_superuser)
            response = self.c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            user.revoke_all(self.vm)
            self.c.logout()

            del data[i]

    def test_view_modify_quota_over(self):
        args = (self.cluster.slug, self.vm.hostname)
        url = '/cluster/%s/%s/edit' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()
        user.grant('modify', self.vm)
        profile = user.get_profile()
        self.vm.owner = profile
        self.vm.save()

        self.cluster.set_quota(profile, dict(ram=1000, disk=2000,
                                             virtual_cpus=10))

        ## POST
        os_list = cluster_os_list(self.cluster)
        data = dict(vcpus=2000,
            acpi=True,
            disk_cache='default',
            initrd_path='',
            kernel_args='ro',
            kvm_flag='',
            mem_path='',
            migration_downtime=30,
            security_domain='',
            security_model='none',
            usb_mouse='',
            use_chroot=False,
            use_localtime=False,
            vnc_bind_address='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_count_original=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')

        user.grant('modify', self.vm)
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        self.assertFalse(user.is_superuser)
        session = self.c.session
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code) # 302 if success (BAD)
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(self.vm)
        self.c.logout()

    def test_view_modify_confirm_quota_over(self):
        args = (self.cluster.slug, self.vm.hostname)
        url = '/cluster/%s/%s/edit/confirm' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()
        user.grant('modify', self.vm)
        profile = user.get_profile()
        self.vm.owner = profile
        self.vm.save()

        self.cluster.set_quota(profile, dict(ram=1000, disk=2000,
                                             virtual_cpus=10))

        os_list = cluster_os_list(self.cluster)
        edit_form = dict(vcpus=2000,
            acpi=True,
            disk_cache='default',
            initrd_path='',
            kernel_args='ro',
            kvm_flag='',
            mem_path='',
            migration_downtime=30,
            security_domain='',
            security_model='none',
            usb_mouse='',
            use_chroot=False,
            use_localtime=False,
            vnc_bind_address='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_count_original=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')
        data = {'rapi_dict':json.dumps(edit_form), 'save':True}

        # regular user
        self.assertTrue(self.c.login(username=user.username,
                                     password='secret2'))
        session = self.c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = self.c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        self.c.logout()


class TestVirtualMachineDeleteViews(TestVirtualMachineViewsBase):
    """
    Test the virtual machine deletion view in a variety of ways.
    """

    def setUp(self):
        super(TestVirtualMachineDeleteViews, self).setUp()
        self.url = '/cluster/%s/%s/delete'
        self.args = (self.cluster.slug, self.vm.hostname)

    def test_view_delete_anonymous(self):
        response = self.c.get(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_view_delete_unauthorized(self):
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(self.url % self.args)
        self.assertEqual(403, response.status_code)

    def test_view_delete_invalid_vm(self):
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(self.url % (self.cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)

    def test_view_delete_get_authorized_remove(self):
        self.user.grant('remove', self.vm)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(self.url % self.args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())

    def test_view_delete_get_authorized_admin(self):
        self.user.grant('admin', self.vm)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(self.url % self.args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())

    def test_view_delete_get_authorized_cluster_admin(self):
        self.user.grant('admin', self.cluster)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(self.url % self.args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())

    def test_view_delete_get_superuser(self):
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        response = self.c.get(self.url % self.args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())

    def test_view_delete_post_superuser(self):
        self.assertTrue(self.c.login(username=self.superuser.username,
                                     password='secret'))
        self.vm.rapi.GetJobStatus.response = JOB_RUNNING
        response = self.c.post(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        qs = VirtualMachine.objects.filter(id=self.vm.id)
        pending_delete, job_id = qs.values('pending_delete', 'last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)

    def test_view_delete_post_cluster_admin(self):
        self.user.grant('admin', self.cluster)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response,
                                'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        qs = VirtualMachine.objects.filter(id=self.vm.id)
        pending_delete, job_id = qs.values('pending_delete', 'last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)

    def test_view_delete_post_admin(self):
        self.user.grant('admin', self.vm)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        qs = VirtualMachine.objects.filter(id=self.vm.id)
        pending_delete, job_id = qs.values('pending_delete', 'last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)

    def test_view_delete_post_vm_remove(self):
        self.user.grant('remove', self.vm)
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        qs = VirtualMachine.objects.filter(id=self.vm.id)
        pending_delete, job_id = qs.values('pending_delete', 'last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)


class TestVirtualMachineReinstallViews(TestVirtualMachineViewsBase):

    def test_view_reinstall(self):
        """
        Tests view for reinstalling virtual machines
        """
        url = '/cluster/%s/%s/reinstall'
        args = (self.cluster.slug, self.vm.hostname)

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(url % args)
        self.assertEqual(403, response.status_code)

        # invalid vm
        response = self.c.get(url % (self.cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)

        # authorized GET (vm remove permissions)
        self.user.grant('remove', self.vm)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        self.user.revoke_all(self.vm)

        # authorized GET (vm admin permissions)
        self.user.grant('admin', self.vm)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        self.user.revoke_all(self.cluster)

        # authorized GET (cluster admin permissions)
        self.user.grant('admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())
        self.user.revoke_all(self.cluster)

        # authorized GET (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=self.vm.id).exists())

        #authorized POST (superuser)
        response = self.c.post(url % args)
        self.assertEqual(302, response.status_code)
        self.user.is_superuser = False
        self.user.save()
        self.vm.save()

        #authorized POST (cluster admin)
        self.user.grant('admin', self.cluster)
        response = self.c.post(url % args)
        self.assertEqual(302, response.status_code)
        self.user.revoke_all(self.cluster)

        #authorized POST (vm admin)
        self.vm.save()
        self.user.grant('admin', self.vm)
        response = self.c.post(url % args)
        self.assertEqual(302, response.status_code)
        self.vm.save()
        self.user.revoke_all(self.vm)

        #authorized POST (cluster admin)
        self.vm.save()
        self.user.grant('remove', self.vm)
        response = self.c.post(url % args)
        self.assertEqual(302, response.status_code)
        self.vm.save()
        self.user.revoke_all(self.vm)


class TestVirtualMachineRenameViews(TestVirtualMachineViewsBase):

    def test_view_rename_get(self):
        """
        VM rename GET requests should have the standard responses.
        """

        url = "/cluster/%s/%s/rename/"
        args = (self.cluster.slug, self.vm.hostname)
        template = 'ganeti/virtual_machine/rename.html'
        users =[self.superuser, self.cluster_admin, self.vm_admin,
                self.vm_modify]
        denied = [self.cluster_migrate]

        # test GET requests
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, template=template)
        self.assert_403(url, args, denied)

    def test_view_rename_post(self):
        """
        VM rename POST requests should have the standard responses.
        """

        url = "/cluster/%s/%s/rename/"
        args = (self.cluster.slug, self.vm.hostname)
        template_success = 'ganeti/virtual_machine/detail.html'
        users = [self.superuser, self.cluster_admin, self.vm_admin,
                 self.vm_modify]
        denied = [self.cluster_migrate]
        data = {'hostname':'foo.arg.different', 'ip_check':False, 'name_check':False}

        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=self.vm.pk)
            self.assertEqual('foo.arg.different', updated_vm.hostname)
            self.vm.save()

        self.assert_standard_fails(url, args, data, method='post')
        self.assert_200(url, args, users, template_success, data=data,
                        follow=True, method="post", tests=tests)
        self.assert_403(url, args, denied, data=data, method="post")

    def test_view_rename_form(self):
        """
        Tests that form validation is working properly
        """

        url = "/cluster/%s/%s/rename/"
        args = (self.cluster.slug, self.vm.hostname)
        template = 'ganeti/virtual_machine/rename.html'
        data = {'hostname':'foo.arg.different', 'ip_check':False, 'name_check':False}
        errors = ({'hostname': self.vm.hostname},)

        #noinspection PyUnusedLocal
        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=self.vm.pk)
            self.assertEqual(self.vm.hostname, updated_vm.hostname)

        self.assert_view_missing_fields(url, args, data, fields=['hostname'],
                                        template=template, tests=tests)
        self.assert_view_values(url, args, data, errors, template,
                                tests=tests)


class TestVirtualMachineReparentViews(TestVirtualMachineViewsBase):

    def test_view_rename_get(self):
        """
        VM reparent GET requests should have the standard responses.
        """

        url = "/cluster/%s/%s/reparent/"
        args = (self.cluster.slug, self.vm.hostname)
        template = 'ganeti/virtual_machine/reparent.html'
        users =[self.superuser, self.cluster_admin]
        denied = [self.vm_admin, self.vm_modify, self.cluster_migrate]

        # test GET requests
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, template=template)
        self.assert_403(url, args, denied)

    def test_view_rename_post(self):
        """
        VM reparent POST requests should have the standard responses.
        """

        self.vm.owner = self.vm_admin.get_profile()
        self.vm.save()

        url = "/cluster/%s/%s/reparent/"
        args = (self.cluster.slug, self.vm.hostname)
        template_success = 'ganeti/virtual_machine/detail.html'
        users = [self.superuser, self.cluster_admin]
        denied = [self.vm_admin, self.vm_modify, self.cluster_migrate]
        data = {'owner': self.vm_modify.get_profile().pk}

        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=self.vm.pk)
            self.assertEqual(self.vm_modify.get_profile().clusteruser_ptr,
                             updated_vm.owner)

        self.assert_standard_fails(url, args, data, method='post')
        self.assert_200(url, args, users, template_success, data=data,
                        follow=True, method="post", tests=tests)
        self.assert_403(url, args, denied, data=data, method="post")
