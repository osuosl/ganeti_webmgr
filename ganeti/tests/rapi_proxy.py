
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
    'mtime': 1285883187.8692031,
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
        CallProxy.patch(instance, 'StartupInstance', False)
        CallProxy.patch(instance, 'ShutdownInstance', False)
        CallProxy.patch(instance, 'RebootInstance', False)
        CallProxy.patch(instance, 'AddInstanceTags', False)
        CallProxy.patch(instance, 'DeleteInstanceTags', False)
        CallProxy.patch(instance, 'CreateInstance', False, 1)
        
        return instance
    
    def fail(self, *args, **kwargs):
        raise self.error
    
    def __getattribute__(self, key):
        if key in ['GetInstances','GetInstance','GetNodes','GetNode', \
                   'GetInfo', 'StartupInstance', 'ShutdownInstance', \
                   'RebootInstance', 'AddInstanceTags','DeleteInstanceTags', \
                   'GetOperatingSystems', 'CreateInstance'] \
                    and self.error:
            return self.fail
        return super(RapiProxy, self).__getattribute__(key)
    