# Copyright (C) 2010 Oregon State University et al.
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


from .. import client
from . import CallProxy
from .constants import *


class RapiProxy(client.GanetiRapiClient):
    """
    Proxy class for testing RAPI interface without a cluster present.
    This class has methods replaced that will return dummy info
    """
    error = None

    def __new__(cls, *args, **kwargs):
        """
        Each time the RapiProxy is created, monkey patch
        the GanetiRapiClient methods to return static data.
        """
        instance = object.__new__(cls)
        instance.__init__(*args, **kwargs)
        CallProxy.patch(instance, 'GetInstances', False, INSTANCES)
        CallProxy.patch(instance, 'GetInstance', False, INSTANCE)
        CallProxy.patch(instance, 'GetNodes', False, NODES_MAP)
        CallProxy.patch(instance, 'GetNode', False, NODE)
        CallProxy.patch(instance, 'GetInfo', False, INFO)
        CallProxy.patch(instance, 'GetOperatingSystems', False,
                        OPERATING_SYSTEMS)
        CallProxy.patch(instance, 'GetJobStatus', False, JOB_RUNNING)
        CallProxy.patch(instance, 'StartupInstance', False, 1)
        CallProxy.patch(instance, 'ShutdownInstance', False, 1)
        CallProxy.patch(instance, 'RebootInstance', False, 1)
        CallProxy.patch(instance, 'ReinstallInstance', False, 1)
        CallProxy.patch(instance, 'AddInstanceTags', False)
        CallProxy.patch(instance, 'DeleteInstanceTags', False)
        CallProxy.patch(instance, 'CreateInstance', False, 1)
        CallProxy.patch(instance, 'DeleteInstance', False, 1)
        CallProxy.patch(instance, 'ModifyInstance', False, 1)
        CallProxy.patch(instance, 'MigrateInstance', False, 1)
        CallProxy.patch(instance, 'RenameInstance', False, 1)
        CallProxy.patch(instance, 'RedistributeConfig', False, 1)
        CallProxy.patch(instance, 'ReplaceInstanceDisks', False, 1)
        CallProxy.patch(instance, 'SetNodeRole', False, 1)
        CallProxy.patch(instance, 'EvacuateNode', False, 1)
        CallProxy.patch(instance, 'MigrateNode', False, 1)

        return instance

    def fail(self, *args, **kwargs):
        """
        Raise the error set on this object.
        """
        raise self.error

    def __setattr__(self, name, value):
        return super(RapiProxy, self).__setattr__(name, value)

    def __getattribute__(self, key):
        if key in ['GetInstances', 'GetInstance', 'GetNodes', 'GetNode',
                   'GetInfo', 'StartupInstance', 'ShutdownInstance',
                   'RebootInstance', 'AddInstanceTags', 'DeleteInstanceTags',
                   'GetOperatingSystems', 'GetJobStatus', 'CreateInstance',
                   'ReinstallInstance'] \
                and self.error:
            return self.fail
        return super(RapiProxy, self).__getattribute__(key)


class XenRapiProxy(RapiProxy):
    def __new__(cls, *args, **kwargs):
        """
        Inherits from the RapiProxy and extends it to return
        information for Xen clusters instead of Kvm clusters.
        """
        instance = RapiProxy.__new__(cls, *args, **kwargs)
        # Unbind functions that are to be patched
        instance.GetInstances = None
        instance.GetInstance = None
        instance.GetInfo = None
        instance.GetOperatingSystems = None
        CallProxy.patch(instance, 'GetInstances', False, INSTANCES)
        CallProxy.patch(instance, 'GetInstance', False, XEN_PVM_INSTANCE)
        CallProxy.patch(instance, 'GetInfo', False, XEN_INFO)
        CallProxy.patch(instance, 'GetOperatingSystems', False,
                        XEN_OPERATING_SYSTEMS)

        return instance


class XenHvmRapiProxy(XenRapiProxy):
    def __new__(cls, *args, **kwargs):
        """
        Inherits from the RapiProxy and extends it to return
        information for Xen clusters instead of Kvm clusters.
        """
        instance = RapiProxy.__new__(cls, *args, **kwargs)
        # Unbind functions that are to be patched
        instance.GetInstances = None
        instance.GetInstance = None
        instance.GetInfo = None
        instance.GetOperatingSystems = None
        CallProxy.patch(instance, 'GetInstances', False, INSTANCES)
        CallProxy.patch(instance, 'GetInstance', False, XEN_PVM_INSTANCE)
        CallProxy.patch(instance, 'GetInfo', False, XEN_INFO)
        CallProxy.patch(instance, 'GetOperatingSystems', False,
                        XEN_OPERATING_SYSTEMS)
