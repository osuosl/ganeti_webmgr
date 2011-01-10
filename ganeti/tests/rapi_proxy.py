# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.



from ganeti.tests.call_proxy import CallProxy
from util import client


class MethodProxy(object):
    """
    simple callable that returns set data
    """
    def __init__(self, data=None, error=None):
        self.data = data
    
    def __call__(self, *args, **kwargs):
        return self.data

INSTANCES = ['gimager.osuosl.bak', 'gimager2.osuosl.bak']
INSTANCE = {'admin_state': False,
    'beparams': {'auto_balance': True, 'memory': 512, 'vcpus': 2},
    'ctime': 1285799513.4741000,
    'disk.sizes': [5120],
    'disk_template': 'plain',
    'disk_usage': 5120,
    'hvparams': {'acpi': True,
                 'boot_order': 'disk',
                 'cdrom_image_path': '',
                 'disk_cache': 'default',
                 'disk_type': 'paravirtual',
                 'initrd_path': '',
                 'kernel_args': 'ro',
                 'kernel_path': '/root/bzImage',
                 'kvm_flag': '',
                 'migration_downtime': 30,
                 'nic_type': 'paravirtual',
                 'root_path': '/dev/vda2',
                 'security_domain': '',
                 'security_model': 'none',
                 'serial_console': True,
                 'usb_mouse': '',
                 'use_chroot': False,
                 'use_localtime': False,
                 'vhost_net': False,
                 'vnc_bind_address': '0.0.0.0',
                 'vnc_password_file': '',
                 'vnc_tls': False,
                 'vnc_x509_path': '',
                 'vnc_x509_verify': False},
    'mtime': 1285883187.8692000,
    'name': 'gimager.osuosl.bak',
    'network_port': 11165,
    'nic.bridges': ['br42'],
    'nic.ips': [None],
    'nic.links': ['br42'],
    'nic.macs': ['aa:00:00:c5:47:2e'],
    'nic.modes': ['bridged'],
    'oper_ram': '-',
    'oper_state': False,
    'oper_vcpus': '-',
    'os': 'image+gentoo-hardened-cf',
    'pnode': 'gtest1.osuosl.bak',
    'serial_no': 8,
    'snodes': [],
    'status': 'ADMIN_down',
    'tags': [],
    'uuid': '27bac3d3-f634-4dee-aa60-ed2eeb5f2287'}

NODES = ['gtest1.osuosl.bak', 'gtest2.osuosl.bak']
NODES_BULK = [
    {'cnodes': 1,
    'csockets': 1,
    'ctime': None,
    'ctotal': 2,
    'dfree': 56092,
    'drained': False,
    'dtotal': 66460,
    'master_candidate': True,
    'mfree': 1187,
    'mnode': 586,
    'mtime': None,
    'mtotal': 1997,
    'name': 'gtest1.osuosl.bak',
    'offline': False,
    'pinst_cnt': 2,
    'pinst_list': ['gimager.osuosl.bak', 'gimager3.osuosl.bak'],
    'pip': '10.1.0.136',
    'role': 'M',
    'serial_no': 1,
    'sinst_cnt': 0,
    'sinst_list': [],
    'sip': '192.168.16.136',
    'tags': [],
    'uuid': '1fee760b-b240-4d7a-a514-5c9441877a01'},
    {'cnodes': 1,
    'csockets': 1,
    'ctime': None,
    'ctotal': 2,
    'dfree': 56092,
    'drained': False,
    'dtotal': 66460,
    'master_candidate': True,
    'mfree': 1187,
    'mnode': 586,
    'mtime': None,
    'mtotal': 1997,
    'name': 'gtest2.osuosl.bak',
    'offline': False,
    'pinst_cnt': 0,
    'pinst_list': [],
    'pip': '10.1.0.136',
    'role': 'M',
    'serial_no': 1,
    'sinst_cnt': 0,
    'sinst_list': [],
    'sip': '192.168.16.136',
    'tags': [],
    'uuid': '1fee760b-b240-4d7a-a514-5c9441877a01'}
]

NODE = {'cnodes': 1,
    'csockets': 1,
    'ctime': None,
    'ctotal': 2,
    'dfree': 56092,
    'drained': False,
    'dtotal': 66460,
    'master_candidate': True,
    'mfree': 1187,
    'mnode': 586,
    'mtime': None,
    'mtotal': 1997,
    'name': 'gtest1.osuosl.bak',
    'offline': False,
    'pinst_cnt': 2,
    'pinst_list': ['gimager.osuosl.bak', 'gimager3.osuosl.bak'],
    'pip': '10.1.0.136',
    'role': 'M',
    'serial_no': 1,
    'sinst_cnt': 0,
    'sinst_list': [],
    'sip': '192.168.16.136',
    'tags': [],
    'uuid': '1fee760b-b240-4d7a-a514-5c9441877a01'}
INFO = {'architecture': ['64bit', 'x86_64'],
    'beparams': {'default': {'auto_balance': True, 'memory': 512, 'vcpus': 2}},
    'candidate_pool_size': 10,
    'config_version': 2020000,
    'ctime': 1270685309.818239,
    'default_hypervisor': 'kvm',
    'default_iallocator': '',
    'drbd_usermode_helper': None,
    'enabled_hypervisors': ['kvm'],
    'export_version': 0,
    'file_storage_dir': '/var/lib/ganeti-storage/file',
    'hvparams': {'kvm': {'acpi': True,
                         'boot_order': 'disk',
                         'cdrom_image_path': '',
                         'disk_cache': 'default',
                         'disk_type': 'paravirtual',
                         'initrd_path': '',
                         'kernel_args': 'ro',
                         'kernel_path': '',
                         'kvm_flag': '',
                         'migration_bandwidth': 32,
                         'migration_downtime': 30,
                         'migration_mode': 'live',
                         'migration_port': 8102,
                         'nic_type': 'paravirtual',
                         'root_path': '/dev/vda2',
                         'security_domain': '',
                         'security_model': 'none',
                         'serial_console': True,
                         'usb_mouse': '',
                         'use_chroot': False,
                         'use_localtime': False,
                         'vhost_net': False,
                         'vnc_bind_address': '0.0.0.0',
                         'vnc_password_file': '',
                         'vnc_tls': False,
                         'vnc_x509_path': '',
                         'vnc_x509_verify': False}},
    'maintain_node_health': False,
    'master': 'gtest1.osuosl.bak',
    'master_netdev': 'br42',
    'mtime': 1283552454.2998919,
    'name': 'ganeti-test.osuosl.bak',
    'nicparams': {'default': {'link': 'br42', 'mode': 'bridged'}},
    'os_api_version': 20,
    'os_hvp': {},
    'osparams': {},
    'protocol_version': 40,
    'reserved_lvs': [],
    'software_version': '2.2.0~rc1',
    'tags': [],
    'uid_pool': [],
    'uuid': 'a22576ba-9158-4336-8590-a497306f84b9',
    'volume_group_name': 'ganeti'}

OPERATING_SYSTEMS = ['image+debian-osgeo', 'image+ubuntu-lucid']

JOB = {'end_ts': [1291845036, 492131],
 'id': '1',
 'oplog': [[]],
 'opresult': [None],
 'ops': [{'OP_ID': 'OP_INSTANCE_SHUTDOWN',
          'debug_level': 0,
          'dry_run': False,
          'instance_name': 'gimager.osuosl.bak',
          'timeout': 120}],
 'opstatus': ['success'],
 'received_ts': [1291845002, 555722],
 'start_ts': [1291845002, 595336],
 'status': 'success',
 'summary': ['INSTANCE_SHUTDOWN(gimager.osuosl.bak)']}

JOB_RUNNING = {'end_ts': [1291845036, 492131],
 'id': '1',
 'oplog': [[]],
 'opresult': [None],
 'ops': [{'OP_ID': 'OP_INSTANCE_SHUTDOWN',
          'debug_level': 0,
          'dry_run': False,
          'instance_name': 'gimager.osuosl.bak',
          'timeout': 120}],
 'opstatus': ['success'],
 'received_ts': [1291845002, 555722],
 'start_ts': [1291845002, 595336],
 'status': 'running',
 'summary': ['INSTANCE_SHUTDOWN(gimager.osuosl.bak)']}

JOB_ERROR = {'end_ts': [1291836084, 802444],
 'id': '1',
 'oplog': [[]],
 'opresult': [['OpExecError',
               ['Could not reboot instance: Cannot reboot instance gimager.osuosl.bak that is not running']]],
 'ops': [{'OP_ID': 'OP_INSTANCE_REBOOT',
          'debug_level': 0,
          'dry_run': False,
          'ignore_secondaries': False,
          'instance_name': 'gimager.osuosl.bak',
          'reboot_type': 'hard',
          'shutdown_timeout': 120}],
 'opstatus': ['error'],
 'received_ts': [1291836084, 639295],
 'start_ts': [1291836084, 673097],
 'status': 'error',
 'summary': ['INSTANCE_REBOOT(gimager.osuosl.bak)']}


JOB_LOG = {'end_ts': [1292007990, 759365],
 'id': '121061',
 'oplog': [[[1,
             [1292007953, 699881],
             'message',
             ' - INFO: Selected nodes for instance gimager3.osuosl.bak via iallocator hail: gtest2.osuosl.bak'],
            [2,
             [1292007953, 979254],
             'message',
             '* creating instance disks...'],
            [3,
             [1292007954, 276561],
             'message',
             'adding instance gimager3.osuosl.bak to cluster config'],
            [4,
             [1292007954, 357390],
             'message',
             ' - INFO: Waiting for instance gimager3.osuosl.bak to sync disks.'],
            [5,
             [1292007954, 496430],
             'message',
             " - INFO: Instance gimager3.osuosl.bak's disks are in sync."],
            [6,
             [1292007954, 498135],
             'message',
             '* running the instance OS create scripts...'],
            [7, [1292007990, 267330], 'message', '* starting instance...']]],
 'opresult': [['gtest2.osuosl.bak']],
 'ops': [{'OP_ID': 'OP_INSTANCE_CREATE',
          'beparams': {},
          'debug_level': 0,
          'disk_template': 'plain',
          'disks': [{'size': 2000}],
          'dry_run': False,
          'file_driver': 'loop',
          'file_storage_dir': None,
          'force_variant': False,
          'hvparams': {'boot_order': 'disk',
                       'cdrom_image_path': '',
                       'kernel_path': '',
                       'root_path': '/dev/vda2',
                       'serial_console': True},
          'hypervisor': 'kvm',
          'iallocator': 'hail',
          'identify_defaults': False,
          'instance_name': 'gimager3.osuosl.bak',
          'ip_check': True,
          'mode': 'create',
          'name_check': True,
          'nics': [{}],
          'no_install': None,
          'os_type': 'image+ubuntu-maverick',
          'osparams': {},
          'pnode': 'gtest2.osuosl.bak',
          'snode': None,
          'source_handshake': None,
          'source_instance_name': None,
          'source_x509_ca': None,
          'src_node': None,
          'src_path': None,
          'start': True,
          'wait_for_sync': True}],
 'opstatus': ['success'],
 'received_ts': [1292007950, 338883],
 'start_ts': [1292007950, 367402],
 'status': 'success',
 'summary': ['INSTANCE_CREATE(gimager3.osuosl.bak)']}

INSTANCES_BULK = [{'admin_state': False,
    'beparams': {'auto_balance': True, 'memory': 512, 'vcpus': 2},
    'ctime': 1285799513.4741089,
    'disk.sizes': [5120],
    'disk_template': 'plain',
    'disk_usage': 5120,
    'hvparams': {'acpi': True,
                 'boot_order': 'disk',
                 'cdrom_image_path': '',
                 'disk_cache': 'default',
                 'disk_type': 'paravirtual',
                 'initrd_path': '',
                 'kernel_args': 'ro',
                 'kernel_path': '/root/bzImage',
                 'kvm_flag': '',
                 'migration_downtime': 30,
                 'nic_type': 'paravirtual',
                 'root_path': '/dev/vda2',
                 'security_domain': '',
                 'security_model': 'none',
                 'serial_console': True,
                 'usb_mouse': '',
                 'use_chroot': False,
                 'use_localtime': False,
                 'vhost_net': False,
                 'vnc_bind_address': '0.0.0.0',
                 'vnc_password_file': '',
                 'vnc_tls': False,
                 'vnc_x509_path': '',
                 'vnc_x509_verify': False},
    'mtime': 1285883187.8692000,
    'name': 'vm1.osuosl.bak',
    'network_port': 11165,
    'nic.bridges': ['br42'],
    'nic.ips': [None],
    'nic.links': ['br42'],
    'nic.macs': ['aa:00:00:c5:47:2e'],
    'nic.modes': ['bridged'],
    'oper_ram': '-',
    'oper_state': False,
    'oper_vcpus': '-',
    'os': 'image+gentoo-hardened-cf',
    'pnode': 'gtest1.osuosl.bak',
    'serial_no': 8,
    'snodes': [],
    'status': 'running',
    'tags': [],
    'uuid': '27bac3d3-f634-4dee-aa60-ed2eeb5f2287'},
    {'admin_state': False,
    'beparams': {'auto_balance': True, 'memory': 512, 'vcpus': 2},
    'ctime': 1285799513.4741089,
    'disk.sizes': [5120],
    'disk_template': 'plain',
    'disk_usage': 5120,
    'hvparams': {'acpi': True,
                 'boot_order': 'disk',
                 'cdrom_image_path': '',
                 'disk_cache': 'default',
                 'disk_type': 'paravirtual',
                 'initrd_path': '',
                 'kernel_args': 'ro',
                 'kernel_path': '/root/bzImage',
                 'kvm_flag': '',
                 'migration_downtime': 30,
                 'nic_type': 'paravirtual',
                 'root_path': '/dev/vda2',
                 'security_domain': '',
                 'security_model': 'none',
                 'serial_console': True,
                 'usb_mouse': '',
                 'use_chroot': False,
                 'use_localtime': False,
                 'vhost_net': False,
                 'vnc_bind_address': '0.0.0.0',
                 'vnc_password_file': '',
                 'vnc_tls': False,
                 'vnc_x509_path': '',
                 'vnc_x509_verify': False},
    'mtime': 1285883187.8692000,
    'name': 'vm2.osuosl.bak',
    'network_port': 11165,
    'nic.bridges': ['br42'],
    'nic.ips': [None],
    'nic.links': ['br42'],
    'nic.macs': ['aa:00:00:c5:47:2e'],
    'nic.modes': ['bridged'],
    'oper_ram': '-',
    'oper_state': False,
    'oper_vcpus': '-',
    'os': 'image+gentoo-hardened-cf',
    'pnode': 'gtest1.osuosl.bak',
    'serial_no': 8,
    'snodes': [],
    'status': 'running',
    'tags': [],
    'uuid': '27bac3d3-f634-4dee-aa60-ed2eeb5f2287'}
]


class RapiProxy(client.GanetiRapiClient):
    """
    Proxy class for testing RAPI interface without a cluster present. This class
    has methods replaced that will return dummy info
    """
    error = None
    
    def __new__(klass, *args, **kwargs):
        instance = object.__new__(klass)
        instance.__init__(*args, **kwargs)
        CallProxy.patch(instance, 'GetInstances', False, INSTANCES)
        CallProxy.patch(instance, 'GetInstance', False, INSTANCE)
        CallProxy.patch(instance, 'GetNodes', False, NODES)
        CallProxy.patch(instance, 'GetNode', False, NODE)
        CallProxy.patch(instance, 'GetInfo', False, INFO)
        CallProxy.patch(instance, 'GetOperatingSystems', False, OPERATING_SYSTEMS)
        CallProxy.patch(instance, 'GetJobStatus', False, JOB)
        CallProxy.patch(instance, 'StartupInstance', False, 1)
        CallProxy.patch(instance, 'ShutdownInstance', False, 1)
        CallProxy.patch(instance, 'RebootInstance', False, 1)
        CallProxy.patch(instance, 'ReinstallInstance', False, 1)
        CallProxy.patch(instance, 'AddInstanceTags', False)
        CallProxy.patch(instance, 'DeleteInstanceTags', False)
        CallProxy.patch(instance, 'CreateInstance', False, 1)
        CallProxy.patch(instance, 'DeleteInstance', False, 1)
        
        return instance
    
    def fail(self, *args, **kwargs):
        raise self.error
    
    def __getattribute__(self, key):
        if key in ['GetInstances','GetInstance','GetNodes','GetNode', \
                   'GetInfo', 'StartupInstance', 'ShutdownInstance', \
                   'RebootInstance', 'AddInstanceTags','DeleteInstanceTags', \
                   'GetOperatingSystems', 'GetJobStatus', 'CreateInstance', \
                   'ReinstallInstance' ] \
                    and self.error:
            return self.fail
        return super(RapiProxy, self).__getattribute__(key)
    
