import json

from django.contrib.auth.models import User

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

global c, cluster, vm
global user, user1, superuser, cluster_admin, vm_admin, vm_modify, cluster_migrate


class TestVirtualMachineEditViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_modify(self):
        """
        Test modifying an instance
        """
        vm = globals()['vm']
        args = (cluster.slug, vm.hostname)
        url = '/cluster/%s/%s/edit' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()

        ## GET
        # Anonymous User
        response = c.get(url)
        self.assertEqual(302, response.status_code)

        # User with Modify Permissions
        user.grant('modify', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm('modify', vm))
        self.assertFalse(user.has_perm('admin', vm))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(vm)
        c.logout()

        # User with Admin Permissions
        user.grant('admin', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(vm)
        c.logout()

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(c.login(username=user.username, password='secret2'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        c.logout()
        user.is_superuser = False
        user.save()

        ## POST
        os_list = cluster_os_list(cluster)
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
            vnc_bind_addres='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')

        # Required Values
        user.grant('modify', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        session['os_list'] = os_list
        session.save()
        for property in ['vcpus', 'memory', 'disk_type', 'boot_order',
                         'nic_type']:
            data_ = data.copy()
            del data_[property]
            self.assertFalse(user.is_superuser)
            response = c.post(url, data_)
            # If failure then a field that is not required by the model, but
            #  should be required by the form, is not being required by
            #  the form. See the ModifyVirtualMachineForm.required field.
            self.assertNotEqual(response.context['form'][property].errors, [], msg=property)
            self.assertEqual(200, response.status_code) # 302 if success (BAD)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        c.logout()
        user.revoke_all(vm)


        # Anonymous User
        response = c.post(url, data)
        self.assertEqual(302, response.status_code)

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertTrue(user.is_superuser)
        session = c.session
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        c.logout()
        user.is_superuser = False
        user.save()

        # User without Permissions
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        session = c.session
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(403, response.status_code)
        self.assertTrue(response.context['message'])
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, '403.html')
        c.logout()

        # User with Modify Permissions
        user.grant('modify', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        session = c.session
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        user.revoke_all(vm)
        c.logout()

        # User with Admin Permissions
        user.grant('admin', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        session = c.session
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        user.revoke_all(vm)
        c.logout()

    def test_view_modify_confirm(self):
        """
        Test confirm page for modifying an instance
        """
        vm = globals()['vm']
        args = (cluster.slug, vm.hostname)
        url = '/cluster/%s/%s/edit/confirm' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()

        vm.owner = user.get_profile()
        vm.save()

        os_list = cluster_os_list(cluster)
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
            vnc_bind_addres='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
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
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        # edit_form
        response = c.get(url)
        self.assertEqual(400, response.status_code)
        session['edit_form'] = edit_form
        session.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')

        #session['os_list'] = os_list
        #session.save()
        user.revoke_all(vm)
        user.is_superuser = False
        user.save()
        c.logout()

        ## GET
        # Anonymous User
        response = c.get(url)
        self.assertEqual(302, response.status_code)

        # User with Modify Permissions
        user.grant('modify', vm)
        self.assertFalse(user.is_superuser)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        user.revoke_all(vm)
        c.logout()

        # User with Admin Permissions
        user.grant('admin', vm)
        self.assertFalse(user.is_superuser)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        user.revoke_all(vm)
        c.logout()

        # Superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        c.logout()
        user.is_superuser = False
        user.save()

        ## POST
        data = {'rapi_dict':json.dumps(edit_form)}
        # Anonymous User
        response = c.post(url, data)
        self.assertEqual(302, response.status_code)

        for i in ('cancel', 'edit', 'save', 'reboot'):
            data[i] = True

            # Superuser
            user.is_superuser = True
            user.save()
            self.assertTrue(c.login(username=user.username, password='secret2'))
            session = c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertTrue(user.is_superuser)
            response = c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            c.logout()
            user.is_superuser = False
            user.save()

            # User without Permissions
            self.assertTrue(c.login(username=user.username, password='secret2'))
            self.assertFalse(user.is_superuser)
            response = c.post(url, data)
            self.assertEqual(403, response.status_code)
            self.assertTrue(response.context['message'])
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, '403.html')
            c.logout()

            # User with Modify Permissions
            user.grant('modify', vm)
            user.grant('power', vm)
            self.assertTrue(c.login(username=user.username, password='secret2'))
            session = c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertFalse(user.is_superuser)
            response = c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            user.revoke_all(vm)
            c.logout()

            # User with Admin Permissions
            user.grant('admin', vm)
            self.assertTrue(c.login(username=user.username, password='secret2'))
            session = c.session
            session['edit_form'] = edit_form
            session['os_list'] = os_list
            session.save()
            self.assertFalse(user.is_superuser)
            response = c.post(url, data)
            self.assertEqual(302, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            user.revoke_all(vm)
            c.logout()

            del data[i]

    def test_view_modify_quota_over(self):
        vm = globals()['vm']
        args = (cluster.slug, vm.hostname)
        url = '/cluster/%s/%s/edit' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()
        user.grant('modify', vm)
        profile = user.get_profile()
        vm.owner = profile
        vm.save()

        cluster.set_quota(profile, dict(ram=1000, disk=2000, virtual_cpus=10))

        ## POST
        os_list = cluster_os_list(cluster)
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
            vnc_bind_addres='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')

        user.grant('modify', vm)
        self.assertTrue(c.login(username=user.username, password='secret2'))
        self.assertFalse(user.is_superuser)
        session = c.session
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(200, response.status_code) # 302 if success (BAD)
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_kvm.html')
        user.revoke_all(vm)
        c.logout()

    def test_view_modify_confirm_quota_over(self):
        vm = globals()['vm']
        args = (cluster.slug, vm.hostname)
        url = '/cluster/%s/%s/edit/confirm' % args

        user = User(id=52, username='modifier')
        user.set_password('secret2')
        user.save()
        user.grant('modify', vm)
        profile = user.get_profile()
        vm.owner = profile
        vm.save()

        cluster.set_quota(profile, dict(ram=1000, disk=2000, virtual_cpus=10))

        os_list = cluster_os_list(cluster)
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
            vnc_bind_addres='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')
        data = {'rapi_dict':json.dumps(edit_form), 'save':True}

        # regular user
        self.assertTrue(c.login(username=user.username, password='secret2'))
        session = c.session
        session['edit_form'] = edit_form
        session['os_list'] = os_list
        session.save()
        response = c.post(url, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/edit_confirm.html')
        c.logout()

        
class TestVirtualMachineDeleteViews(TestVirtualMachineViewsBase):
    context = globals()

    def test_view_delete(self):
        """
        Tests view for deleting virtual machines
        """
        url = '/cluster/%s/%s/delete'
        args = (cluster.slug, vm.hostname)

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.post(url % args)
        self.assertEqual(403, response.status_code)

        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)

        # authorized GET (vm remove permissions)
        user.grant('remove', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(vm)

        # authorized GET (vm admin permissions)
        user.grant('admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(cluster)

        # authorized GET (cluster admin permissions)
        user.grant('admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(cluster)

        # authorized GET (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())

        #authorized POST (superuser)
        user1.grant('power', vm)
        vm.rapi.GetJobStatus.response = JOB_RUNNING
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        pending_delete, job_id = VirtualMachine.objects.filter(id=vm.id).values('pending_delete','last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)
        user.is_superuser = False
        user.save()
        vm.save()

        #authorized POST (cluster admin)
        user.grant('admin', cluster)
        user1.grant('power', vm)
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        pending_delete, job_id = VirtualMachine.objects.filter(id=vm.id).values('pending_delete','last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)
        user.revoke_all(cluster)

        #authorized POST (vm admin)
        vm.save()
        user.grant('admin', vm)
        user1.grant('power', vm)
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        pending_delete, job_id = VirtualMachine.objects.filter(id=vm.id).values('pending_delete','last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)
        vm.save()
        user.revoke_all(vm)

        #authorized POST (cluster admin)
        vm.save()
        user.grant('remove', vm)
        user1.grant('power', vm)
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/delete_status.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        pending_delete, job_id = VirtualMachine.objects.filter(id=vm.id).values('pending_delete','last_job_id')[0]
        self.assertTrue(pending_delete)
        self.assertTrue(job_id)
        vm.save()
        user.revoke_all(vm)


class TestVirtualMachineReinstallViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_reinstall(self):
        """
        Tests view for reinstalling virtual machines
        """
        url = '/cluster/%s/%s/reinstall'
        args = (cluster.slug, vm.hostname)

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=user.username, password='secret'))
        response = c.post(url % args)
        self.assertEqual(403, response.status_code)

        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)

        # authorized GET (vm remove permissions)
        user.grant('remove', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(vm)

        # authorized GET (vm admin permissions)
        user.grant('admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(cluster)

        # authorized GET (cluster admin permissions)
        user.grant('admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())
        user.revoke_all(cluster)

        # authorized GET (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/reinstall.html')
        self.assertTrue(VirtualMachine.objects.filter(id=vm.id).exists())

        #authorized POST (superuser)
        response = c.post(url % args)
        self.assertEqual(302, response.status_code)
        user.is_superuser = False
        user.save()
        vm.save()

        #authorized POST (cluster admin)
        user.grant('admin', cluster)
        response = c.post(url % args)
        self.assertEqual(302, response.status_code)
        user.revoke_all(cluster)

        #authorized POST (vm admin)
        vm.save()
        user.grant('admin', vm)
        response = c.post(url % args)
        self.assertEqual(302, response.status_code)
        vm.save()
        user.revoke_all(vm)

        #authorized POST (cluster admin)
        vm.save()
        user.grant('remove', vm)
        response = c.post(url % args)
        self.assertEqual(302, response.status_code)
        vm.save()
        user.revoke_all(vm)


class TestVirtualMachineRenameViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_rename_get(self):
        """
        VM rename GET requests should have the standard responses.
        """

        url = "/cluster/%s/%s/rename/"
        args = (cluster.slug, vm.hostname)
        template = 'ganeti/virtual_machine/rename.html'
        users =[superuser, cluster_admin, vm_admin, vm_modify]
        denied = [cluster_migrate]

        # test GET requests
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, template=template)
        self.assert_403(url, args, denied)

    def test_view_rename_post(self):
        """
        VM rename POST requests should have the standard responses.
        """

        url = "/cluster/%s/%s/rename/"
        args = (cluster.slug, vm.hostname)
        template_success = 'ganeti/virtual_machine/detail.html'
        users = [superuser, cluster_admin, vm_admin, vm_modify]
        denied = [cluster_migrate]
        data = {'hostname':'foo.arg.different', 'ip_check':False, 'name_check':False}

        #noinspection PyUnusedLocal
        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=vm.pk)
            self.assertEqual('foo.arg.different', updated_vm.hostname)
            vm.save()

        self.assert_standard_fails(url, args, data, method='post')
        self.assert_200(url, args, users, template_success, data=data, follow=True, method="post", tests=tests)
        self.assert_403(url, args, denied, data=data, method="post")

    def test_view_rename_form(self):
        """
        Tests that form validation is working properly
        """

        url = "/cluster/%s/%s/rename/"
        args = (cluster.slug, vm.hostname)
        template = 'ganeti/virtual_machine/rename.html'
        data = {'hostname':'foo.arg.different', 'ip_check':False, 'name_check':False}
        errors = ({'hostname':vm.hostname},)

        #noinspection PyUnusedLocal
        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=vm.pk)
            self.assertEqual(vm.hostname, updated_vm.hostname)

        self.assert_view_missing_fields(url, args, data, fields=['hostname'], template=template, tests=tests)
        self.assert_view_values(url, args, data, errors, template, tests=tests)


class TestVirtualMachineReparentViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_rename_get(self):
        """
        VM reparent GET requests should have the standard responses.
        """

        url = "/cluster/%s/%s/reparent/"
        args = (cluster.slug, vm.hostname)
        template = 'ganeti/virtual_machine/reparent.html'
        users =[superuser, cluster_admin]
        denied = [vm_admin, vm_modify, cluster_migrate]

        # test GET requests
        self.assert_standard_fails(url, args)
        self.assert_200(url, args, users, template=template)
        self.assert_403(url, args, denied)

    def test_view_rename_post(self):
        """
        VM reparent POST requests should have the standard responses.
        """

        vm.owner = vm_admin.get_profile()
        vm.save()

        url = "/cluster/%s/%s/reparent/"
        args = (cluster.slug, vm.hostname)
        template_success = 'ganeti/virtual_machine/detail.html'
        users = [superuser, cluster_admin]
        denied = [vm_admin, vm_modify, cluster_migrate]
        data = {'owner':vm_modify.get_profile().pk}

        #noinspection PyUnusedLocal
        def tests(user, response):
            updated_vm = VirtualMachine.objects.get(pk=vm.pk)
            self.assertEqual(vm_modify.get_profile().clusteruser_ptr, updated_vm.owner)

        self.assert_standard_fails(url, args, data, method='post')
        self.assert_200(url, args, users, template_success, data=data, follow=True, method="post", tests=tests)
        self.assert_403(url, args, denied, data=data, method="post")
