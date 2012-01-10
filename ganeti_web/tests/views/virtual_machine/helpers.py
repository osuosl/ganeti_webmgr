import json

from django.contrib.auth.models import Group
from django.test import TestCase

from object_permissions import grant

from ganeti_web import models
from ganeti_web.tests.rapi_proxy import INFO
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase
from ganeti_web.utilities import os_prettify

__all__ = ['TestVirtualMachineCreateHelpers', 'TestVirtualMachineHelpers']

Cluster = models.Cluster


class TestVirtualMachineCreateHelpers(TestVirtualMachineViewsBase):

    def test_view_cluster_choices(self):
        """
        Test retrieving list of clusters a user or usergroup has access to
        """
        url = '/vm/add/choices/'
        Cluster.objects.all().delete()
        cluster0 = Cluster(hostname='user.create_vm', slug='user_create_vm')
        cluster0.save()
        cluster1 = Cluster(hostname='user.admin', slug='user_admin')
        cluster1.save()
        cluster2 = Cluster(hostname='superuser', slug='superuser')
        cluster2.save()
        cluster3 = Cluster(hostname='group.create_vm', slug='group_create_vm')
        cluster3.save()
        cluster4 = Cluster(hostname='group.admin', slug='group_admin')
        cluster4.save()
        cluster5 = Cluster(hostname='no.perms.on.this.group', slug='no_perms')
        cluster5.save()
        # cluster ids are 1 through 6

        # Set each cluster info and update
        for cluster in (cluster0, cluster1, cluster2, cluster3, cluster4, cluster5):
            cluster.username = self.user.username
            cluster.password = 'foobar'
            cluster.info = INFO
            cluster.save()

        self.group.user_set.add(self.user)
        group1 = Group(id=43, name='testing_group2')
        group1.save()
        group1.grant('admin',cluster5)

        # anonymous user
        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        self.assertTrue(self.c.login(username=self.user.username, password='secret'))

        # Invalid ClusterUser
        response = self.c.get(url, {'clusteruser_id':-1})
        self.assertEqual(404, response.status_code)

        # create_vm permission through a group
        self.group.grant('create_vm', cluster3)
        response = self.c.get(url, {'clusteruser_id':
                                    self.group.organization.id})
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assertTrue([cluster3.id,'group.create_vm'] in clusters)
        self.assertEqual(1, len(clusters))

        # admin permission through a group
        self.group.grant('admin', cluster4)
        response = self.c.get(url, {'clusteruser_id':
                                    self.group.organization.id})
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assertTrue([cluster3.id,'group.create_vm'] in clusters)
        self.assertTrue([cluster4.id,'group.admin'] in clusters)
        self.assertEqual(2, len(clusters))

        # create_vm permission on the user
        self.user.grant('create_vm', cluster0)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assertTrue([cluster0.id,'user.create_vm'] in clusters)
        self.assertEqual(1, len(clusters), clusters)

        # admin permission on the user
        self.user.grant('admin', cluster1)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assertTrue([cluster0.id,'user.create_vm'] in clusters)
        self.assertTrue([cluster1.id,'user.admin'] in clusters)
        self.assertEqual(2, len(clusters))

        # Superusers see everything
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        clusters = json.loads(response.content)
        self.assertTrue([cluster0.id,'user.create_vm'] in clusters)
        self.assertTrue([cluster1.id,'user.admin'] in clusters)
        self.assertTrue([cluster2.id,'superuser'] in clusters, clusters)
        self.assertTrue([cluster3.id,'group.create_vm'] in clusters)
        self.assertTrue([cluster4.id,'group.admin'] in clusters, clusters)
        self.assertTrue([cluster5.id,'no.perms.on.this.group'] in clusters)
        self.assertEqual(6, len(clusters))

    def test_view_cluster_options(self):
        """
        Test retrieving list of options a cluster has for vms
        """
        url = '/vm/add/options/?cluster_id=%s'
        args = self.cluster.id

        # anonymous user
        response = self.c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # invalid cluster
        response = self.c.get(url % "-4")
        self.assertEqual(404, response.status_code)

        # authorized (create_vm)
        grant(self.user, 'create_vm', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(set([u'gtest1.osuosl.bak', u'gtest2.osuosl.bak',
                              u'gtest3.osuosl.bak']), set(content['nodes']))
        self.assertEqual(content["os"],
            [[u'Image',
                [[u'image+debian-osgeo', u'Debian Osgeo'],
                [u'image+ubuntu-lucid', u'Ubuntu Lucid']]
            ]]
        )
        self.user.revoke_all(self.cluster)

        # authorized (cluster admin)
        grant(self.user, 'admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)

        self.assertEqual(set([u'gtest1.osuosl.bak', u'gtest2.osuosl.bak',
                              u'gtest3.osuosl.bak']), set(content['nodes']))
        self.assertEqual(content["os"],
            [[u'Image',
                [[u'image+debian-osgeo', u'Debian Osgeo'],
                [u'image+ubuntu-lucid', u'Ubuntu Lucid']]
            ]]
        )
        self.user.revoke_all(self.cluster)

        # authorized (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(set([u'gtest1.osuosl.bak', u'gtest2.osuosl.bak',
                              u'gtest3.osuosl.bak']), set(content['nodes']))
        self.assertEqual(content["os"],
            [[u'Image',
                [[u'image+debian-osgeo', u'Debian Osgeo'],
                [u'image+ubuntu-lucid', u'Ubuntu Lucid']]
            ]]
        )

    def test_view_cluster_defaults(self):
        """
        Test retrieval of dict of default parameters set on cluster
        """
        url = '/vm/add/defaults/?cluster_id=%s'
        args = self.cluster.id
        """
        expected = dict(
            boot_order='disk',
            memory=512,
            nic_type='paravirtual',
            root_path='/dev/vda2',
            hypervisors=['kvm'],
            serial_console=True,
            cdrom_image_path='',
            disk_type ='paravirtual',
            nic_link ='br42',
            nic_mode='bridged',
            vcpus=2,
            iallocator='',
            kernel_path=''
        )
        """
        expected = dict(
            nic_type='paravirtual',
            use_chroot=False,
            migration_port=8102,
            vnc_bind_address='0.0.0.0',
            nic_mode='bridged',
            usb_mouse='',
            hypervisors=[['kvm', 'kvm']],
            migration_downtime=30,
            nic_types=[
                ['', '---------'],
                ['rtl8139', 'rtl8139'],
                ['ne2k_isa', 'ne2k_isa'],
                ['ne2k_pci', 'ne2k_pci'],
                ['paravirtual', 'paravirtual'],
                ['i82551', 'i82551'],
                ['i82557b', 'i82557b'],
                ['i82559er', 'i82559er'],
                ['pcnet', 'pcnet'],
                ['e1000', 'e1000']
            ],
            kernel_args='ro',
            cdrom_image_path='',
            boot_order='disk',
            vhost_net=False,
            disk_types=[
                ['', '---------'],
                ['paravirtual', 'paravirtual'],
                ['ide', 'ide'],
                ['scsi', 'scsi'],
                ['sd', 'sd'],
                ['mtd', 'mtd'],
                ['pflash', 'pflash']
            ],
            initrd_path='',
            disk_cache='default',
            memory=512,
            kernel_path='',
            vnc_x509_path='',
            vnc_x509_verify=False,
            vnc_tls=False,
            use_localtime=False,
            boot_devices=[
                ['disk', 'Hard Disk'],
                ['cdrom', 'CD-ROM'],
                ['network', 'Network']
            ],
            security_domain='',
            serial_console=True,
            kvm_flag='',
            vnc_password_file='',
            migration_bandwidth=32,
            disk_type='paravirtual',
            security_model='none',
            migration_mode='live',
            nic_link='br42',
            hypervisor='kvm',
            root_path='/dev/vda2',
            acpi=True,
            vcpus=2,
            iallocator='',
        )

        #anonymous users
        response = self.c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        #unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        #invalid cluster
        response = self.c.get(url % "-2")
        self.assertEqual(404, response.status_code)

        #authorized (create_vm)
        grant(self.user, 'create_vm', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(expected, content, msg=content)
        self.user.revoke_all(self.cluster)

        #authorized (admin)
        grant(self.user, 'admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(expected, content)
        self.user.revoke_all(self.cluster)

        #authorized (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(expected, content)
        self.user.is_superuser = False
        self.user.save()


class TestVirtualMachineHelpers(TestCase):

    def test_os_prettify(self):
        """
        Test the os_prettify() helper function.
        """

        # Test a single entry.
        self.assertEqual(os_prettify(["hurp+durp"]),
            [
                ("Hurp",
                    [("hurp+durp", "Durp")]
                )
            ])

    def test_os_prettify_multiple(self):
        """
        Test os_prettify()'s ability to handle multiple entries, including two
        entries on the same category.
        """

        self.assertEqual(
            os_prettify([
                "image+obonto-hungry-hydralisk",
                "image+fodoro-core",
                "dobootstrop+dobion-lotso",
            ]), [
                ("Dobootstrop", [
                    ("dobootstrop+dobion-lotso", "Dobion Lotso"),
                ]),
                ("Image", [
                    ("image+obonto-hungry-hydralisk",
                        "Obonto Hungry Hydralisk"),
                    ("image+fodoro-core", "Fodoro Core"),
                ]),
            ])

    def test_os_prettify_2517(self):
        """
        Test #2157 compliance.

        This example should still parse, but in a weird way. Better than
        nothing, though.
        """

        self.assertEqual(os_prettify(["debian-pressed+ia32"]),
            [('Debian-pressed', [('debian-pressed+ia32', 'Ia32')])])

    def test_os_prettify_2517_unknown(self):
        """
        Test #2157 compliance.

        This example wasn't part of the bug; it was constructed to show off
        the fix for #2157.
        """

        self.assertEqual(os_prettify(["deb-ver1", "noop"]),
            [
                ("Unknown", [
                    ("deb-ver1", "deb-ver1"),
                    ("noop", "noop"),
                ]),
            ])
