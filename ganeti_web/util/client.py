# Copyright (C) 2010, 2011 Google Inc.
# Copyright (c) 2012 Oregon State University Open Source Lab
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


"""
Ganeti RAPI client.
"""

# No Ganeti-specific modules should be imported. The RAPI client is supposed
# to be standalone.

import logging
import simplejson as json
import socket

import requests


GANETI_RAPI_PORT = 5080
GANETI_RAPI_VERSION = 2

REPLACE_DISK_PRI = "replace_on_primary"
REPLACE_DISK_SECONDARY = "replace_on_secondary"
REPLACE_DISK_CHG = "replace_new_secondary"
REPLACE_DISK_AUTO = "replace_auto"

NODE_EVAC_PRI = "primary-only"
NODE_EVAC_SEC = "secondary-only"
NODE_EVAC_ALL = "all"

NODE_ROLE_DRAINED = "drained"
NODE_ROLE_MASTER_CANDIATE = "master-candidate"
NODE_ROLE_MASTER = "master"
NODE_ROLE_OFFLINE = "offline"
NODE_ROLE_REGULAR = "regular"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_WAITING = "waiting"
JOB_STATUS_CANCELING = "canceling"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_CANCELED = "canceled"
JOB_STATUS_SUCCESS = "success"
JOB_STATUS_ERROR = "error"
JOB_STATUS_FINALIZED = frozenset([
  JOB_STATUS_CANCELED,
  JOB_STATUS_SUCCESS,
  JOB_STATUS_ERROR,
  ])
JOB_STATUS_ALL = frozenset([
  JOB_STATUS_QUEUED,
  JOB_STATUS_WAITING,
  JOB_STATUS_CANCELING,
  JOB_STATUS_RUNNING,
  ]) | JOB_STATUS_FINALIZED

# Legacy name
JOB_STATUS_WAITLOCK = JOB_STATUS_WAITING

# Internal constants
_REQ_DATA_VERSION_FIELD = "__version__"
_INST_NIC_PARAMS = frozenset(["mac", "ip", "mode", "link"])
_INST_CREATE_V0_DISK_PARAMS = frozenset(["size"])
_INST_CREATE_V0_PARAMS = frozenset([
    "os", "pnode", "snode", "iallocator", "start", "ip_check", "name_check",
    "hypervisor", "file_storage_dir", "file_driver", "dry_run",
])
_INST_CREATE_V0_DPARAMS = frozenset(["beparams", "hvparams"])

# Feature strings
INST_CREATE_REQV1 = "instance-create-reqv1"
INST_REINSTALL_REQV1 = "instance-reinstall-reqv1"
NODE_MIGRATE_REQV1 = "node-migrate-reqv1"
NODE_EVAC_RES1 = "node-evac-res1"

# Old feature constant names in case they're references by users of this module
_INST_CREATE_REQV1 = INST_CREATE_REQV1
_INST_REINSTALL_REQV1 = INST_REINSTALL_REQV1
_NODE_MIGRATE_REQV1 = NODE_MIGRATE_REQV1
_NODE_EVAC_RES1 = NODE_EVAC_RES1

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "user-agent": "Ganeti RAPI Client",
}


class ClientError(Exception):
    """
    Base error class for this module.
    """


class CertificateError(ClientError):
    """
    Raised when a problem is found with the SSL certificate.
    """


class GanetiApiError(ClientError):
    """
    Generic error raised from Ganeti API.
    """

    def __init__(self, msg, code=None):
        ClientError.__init__(self, msg)
        self.code = code


def prepare_query(query):
    """
    Prepare a query object for the RAPI.

    RAPI has lots of curious rules for coercing values.

    This function operates on dicts in-place and has no return value.

    @type query: dict
    @param query: Query arguments
    """

    for name in query:
        value = query[name]

        # None is sent as an empty string.
        if value is None:
            query[name] = ""

        # Booleans are sent as 0 or 1.
        elif isinstance(value, bool):
            query[name] = int(value)

        # XXX shouldn't this just check for basestring instead?
        elif isinstance(value, dict):
            raise ValueError("Invalid query data type %r" %
                             type(value).__name__)


class GanetiRapiClient(object): # pylint: disable-msg=R0904
    """
    Ganeti RAPI client.
    """

    _json_encoder = json.JSONEncoder(sort_keys=True)

    def __init__(self, host, port=GANETI_RAPI_PORT, username=None,
                 password=None, timeout=60, logger=logging):
        """
        Initializes this class.

        @type host: string
        @param host: the ganeti cluster master to interact with
        @type port: int
        @param port: the port on which the RAPI is running (default is 5080)
        @type username: string
        @param username: the username to connect with
        @type password: string
        @param password: the password to connect with
        @param logger: Logging object
        """

        if username is not None and password is None:
            raise ClientError("Password not specified")
        elif password is not None and username is None:
            raise ClientError("Specified password without username")

        self.username = username
        self.password = password
        self.timeout = timeout
        self._logger = logger

        try:
            socket.inet_pton(socket.AF_INET6, host)
            address = "[%s]:%s" % (host, port)
        # ValueError can happen too, so catch it as well for the IPv4
        # fallback.
        except (socket.error, ValueError):
            address = "%s:%s" % (host, port)

        self._base_url = "https://%s" % address

    def _SendRequest(self, method, path, query=None, content=None):
        """
        Sends an HTTP request.

        This constructs a full URL, encodes and decodes HTTP bodies, and
        handles invalid responses in a pythonic way.

        @type method: string
        @param method: HTTP method to use
        @type path: string
        @param path: HTTP URL path
        @type query: list of two-tuples
        @param query: query arguments to pass to urllib.urlencode
        @type content: str or None
        @param content: HTTP body content

        @rtype: object
        @return: JSON-Decoded response

        @raises GanetiApiError: If an invalid response is returned
        """

        if not path.startswith("/"):
            raise ClientError("Implementation error: Called with bad path %s"
                              % path)

        kwargs = {
            "headers": headers,
            "timeout": self.timeout,
            "verify": False,
        }

        if self.username and self.password:
            kwargs["auth"] = self.username, self.password

        if content is not None:
            kwargs["data"] = self._json_encoder.encode(content)

        if query:
            prepare_query(query)
            kwargs["params"] = query

        url = self._base_url + path

        self._logger.debug("Sending request to %s %s", url, kwargs)
        # print "Sending request to %s %s" % (url, kwargs)

        try:
            r = requests.request(method, url, **kwargs)
        except requests.ConnectionError:
            raise GanetiApiError("Couldn't connect to %s" % self._base_url)
        except requests.Timeout:
            raise GanetiApiError("Timed out connecting to %s" %
                                 self._base_url)

        if r.status_code != requests.codes.ok:
            raise GanetiApiError(str(r.status_code), code=r.status_code)

        if r.content:
            return json.loads(r.content)
        else:
            return None

    def GetVersion(self):
        """
        Gets the Remote API version running on the cluster.

        @rtype: int
        @return: Ganeti Remote API version
        """

        return self._SendRequest("get", "/version")

    def GetFeatures(self):
        """
        Gets the list of optional features supported by RAPI server.

        @rtype: list
        @return: List of optional features
        """

        try:
            return self._SendRequest("get", "/%s/features" % GANETI_RAPI_VERSION)
        except GanetiApiError, err:
            # Older RAPI servers don't support this resource. Just return an
            # empty list.
            if err.code == requests.codes.not_found:
                return []
            else:
                raise

    def GetOperatingSystems(self):
        """
        Gets the Operating Systems running in the Ganeti cluster.

        @rtype: list of str
        @return: operating systems
        """

        return self._SendRequest("get", "/%s/os" % GANETI_RAPI_VERSION)

    def GetInfo(self):
        """
        Gets info about the cluster.

        @rtype: dict
        @return: information about the cluster
        """

        return self._SendRequest("get", "/%s/info" % GANETI_RAPI_VERSION,
                                                         None, None)

    def RedistributeConfig(self):
        """
        Tells the cluster to redistribute its configuration files.

        @return: job id

        """
        return self._SendRequest("put", "/%s/redistribute-config" %
                                 GANETI_RAPI_VERSION)

    def ModifyCluster(self, **kwargs):
        """
        Modifies cluster parameters.

        More details for parameters can be found in the RAPI documentation.

        @rtype: int
        @return: job id
        """

        return self._SendRequest("put", "/%s/modify" % GANETI_RAPI_VERSION,
                                 content=kwargs)

    def GetClusterTags(self):
        """
        Gets the cluster tags.

        @rtype: list of str
        @return: cluster tags
        """

        return self._SendRequest("get", "/%s/tags" % GANETI_RAPI_VERSION)

    def AddClusterTags(self, tags, dry_run=False):
        """
        Adds tags to the cluster.

        @type tags: list of str
        @param tags: tags to add to the cluster
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "dry-run": dry_run,
            "tag": tags,
        }

        return self._SendRequest("put", "/%s/tags" % GANETI_RAPI_VERSION,
                                 query=query)

    def DeleteClusterTags(self, tags, dry_run=False):
        """
        Deletes tags from the cluster.

        @type tags: list of str
        @param tags: tags to delete
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        """

        query = {
            "dry-run": dry_run,
            "tag": tags,
        }

        return self._SendRequest("delete", "/%s/tags" % GANETI_RAPI_VERSION,
                                 query=query)

    def GetInstances(self, bulk=False):
        """
        Gets information about instances on the cluster.

        @type bulk: bool
        @param bulk: whether to return all information about all instances

        @rtype: list of dict or list of str
        @return: if bulk is True, info about the instances, else a list of instances
        """

        if bulk:
            return self._SendRequest("get", "/%s/instances" %
                                     GANETI_RAPI_VERSION, query={"bulk": 1})
        else:
            instances = self._SendRequest("get", "/%s/instances" %
                                     GANETI_RAPI_VERSION)
            return [i["id"] for i in instances]

    def GetInstance(self, instance):
        """
        Gets information about an instance.

        @type instance: str
        @param instance: instance whose info to return

        @rtype: dict
        @return: info about the instance
        """

        return self._SendRequest("get", ("/%s/instances/%s" %
                                         (GANETI_RAPI_VERSION, instance)))

    def GetInstanceInfo(self, instance, static=None):
        """
        Gets information about an instance.

        @type instance: string
        @param instance: Instance name
        @rtype: string
        @return: Job ID
        """

        if static is None:
            return self._SendRequest("get", ("/%s/instances/%s/info" %
                                             (GANETI_RAPI_VERSION, instance)))
        else:
            return self._SendRequest("get", ("/%s/instances/%s/info" %
                                             (GANETI_RAPI_VERSION, instance)),
                                     query={"static": static})

    def CreateInstance(self, mode, name, disk_template, disks, nics,
                       **kwargs):
        """
        Creates a new instance.

        More details for parameters can be found in the RAPI documentation.

        @type mode: string
        @param mode: Instance creation mode
        @type name: string
        @param name: Hostname of the instance to create
        @type disk_template: string
        @param disk_template: Disk template for instance (e.g. plain, diskless,
                                                    file, or drbd)
        @type disks: list of dicts
        @param disks: List of disk definitions
        @type nics: list of dicts
        @param nics: List of NIC definitions
        @type dry_run: bool
        @keyword dry_run: whether to perform a dry run
        @type no_install: bool
        @keyword no_install: whether to create without installing OS(true=don't install)

        @rtype: int
        @return: job id
        """

        if _INST_CREATE_REQV1 not in self.GetFeatures():
            raise GanetiApiError("Cannot create Ganeti 2.1-style instances")

        query = {}

        if kwargs.get("dry_run"):
            query["dry-run"] = 1
        if kwargs.get("no_install"):
            query["no-install"] = 1

        # Make a version 1 request.
        body = {
            _REQ_DATA_VERSION_FIELD: 1,
            "mode": mode,
            "name": name,
            "disk_template": disk_template,
            "disks": disks,
            "nics": nics,
        }

        conflicts = set(kwargs.iterkeys()) & set(body.iterkeys())
        if conflicts:
            raise GanetiApiError("Required fields can not be specified as"
                                 " keywords: %s" % ", ".join(conflicts))

        kwargs.pop("dry_run", None)
        body.update(kwargs)

        return self._SendRequest("post", "/%s/instances" %
                                 GANETI_RAPI_VERSION, query=query,
                                 content=body)

    def DeleteInstance(self, instance, dry_run=False):
        """
        Deletes an instance.

        @type instance: str
        @param instance: the instance to delete

        @rtype: int
        @return: job id
        """

        return self._SendRequest("delete", ("/%s/instances/%s" %
                                            (GANETI_RAPI_VERSION, instance)),
                                 query={"dry-run": dry_run})

    def ModifyInstance(self, instance, **kwargs):
        """
        Modifies an instance.

        More details for parameters can be found in the RAPI documentation.

        @type instance: string
        @param instance: Instance name
        @rtype: int
        @return: job id
        """

        return self._SendRequest("put", ("/%s/instances/%s/modify" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 content=kwargs)

    def ActivateInstanceDisks(self, instance, ignore_size=False):
        """
        Activates an instance's disks.

        @type instance: string
        @param instance: Instance name
        @type ignore_size: bool
        @param ignore_size: Whether to ignore recorded size
        @return: job id
        """

        return self._SendRequest("put", ("/%s/instances/%s/activate-disks" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 query={"ignore_size": ignore_size})

    def DeactivateInstanceDisks(self, instance):
        """
        Deactivates an instance's disks.

        @type instance: string
        @param instance: Instance name
        @return: job id
        """

        return self._SendRequest("put", ("/%s/instances/%s/deactivate-disks" %
                                         (GANETI_RAPI_VERSION, instance)))

    def RecreateInstanceDisks(self, instance, disks=None, nodes=None):
        """Recreate an instance's disks.

        @type instance: string
        @param instance: Instance name
        @type disks: list of int
        @param disks: List of disk indexes
        @type nodes: list of string
        @param nodes: New instance nodes, if relocation is desired
        @rtype: string
        @return: job id
        """

        body = {}

        if disks is not None:
            body["disks"] = disks
        if nodes is not None:
            body["nodes"] = nodes

        return self._SendRequest("post", ("/%s/instances/%s/recreate-disks" %
                                          (GANETI_RAPI_VERSION, instance)),
                                 content=body)

    def GrowInstanceDisk(self, instance, disk, amount, wait_for_sync=False):
        """
        Grows a disk of an instance.

        More details for parameters can be found in the RAPI documentation.

        @type instance: string
        @param instance: Instance name
        @type disk: integer
        @param disk: Disk index
        @type amount: integer
        @param amount: Grow disk by this amount (MiB)
        @type wait_for_sync: bool
        @param wait_for_sync: Wait for disk to synchronize
        @rtype: int
        @return: job id
        """

        body = {
            "amount": amount,
            "wait_for_sync": wait_for_sync,
        }

        return self._SendRequest("post", ("/%s/instances/%s/disk/%s/grow" %
                                          (GANETI_RAPI_VERSION, instance,
                                           disk)), content=body)

    def GetInstanceTags(self, instance):
        """
        Gets tags for an instance.

        @type instance: str
        @param instance: instance whose tags to return

        @rtype: list of str
        @return: tags for the instance
        """

        return self._SendRequest("get", ("/%s/instances/%s/tags" %
                                         (GANETI_RAPI_VERSION, instance)))

    def AddInstanceTags(self, instance, tags, dry_run=False):
        """
        Adds tags to an instance.

        @type instance: str
        @param instance: instance to add tags to
        @type tags: list of str
        @param tags: tags to add to the instance
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "tag": tags,
            "dry-run": dry_run,
        }

        return self._SendRequest("put", ("/%s/instances/%s/tags" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def DeleteInstanceTags(self, instance, tags, dry_run=False):
        """
        Deletes tags from an instance.

        @type instance: str
        @param instance: instance to delete tags from
        @type tags: list of str
        @param tags: tags to delete
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        """

        query = {
            "tag": tags,
            "dry-run": dry_run,
        }

        return self._SendRequest("delete", ("/%s/instances/%s/tags" %
                                            (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def RebootInstance(self, instance, reboot_type=None,
                       ignore_secondaries=False, dry_run=False):
        """
        Reboots an instance.

        @type instance: str
        @param instance: instance to rebot
        @type reboot_type: str
        @param reboot_type: one of: hard, soft, full
        @type ignore_secondaries: bool
        @param ignore_secondaries: if True, ignores errors for the secondary node
                while re-assembling disks (in hard-reboot mode only)
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        """

        query = {
            "ignore_secondaries": ignore_secondaries,
            "dry-run": dry_run,
        }

        if reboot_type:
            if reboot_type not in ("hard", "soft", "full"):
                raise GanetiApiError("reboot_type must be one of 'hard',"
                                     " 'soft', or 'full'")
            query["type"] = reboot_type

        return self._SendRequest("post", ("/%s/instances/%s/reboot" %
                                          (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def ShutdownInstance(self, instance, dry_run=False, no_remember=False,
                         timeout=120):
        """
        Shuts down an instance.

        @type instance: str
        @param instance: the instance to shut down
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        @type no_remember: bool
        @param no_remember: if true, will not record the state change
        @rtype: string
        @return: job id
        """

        query = {
            "dry-run": dry_run,
            "no-remember": no_remember,
            "timeout": timeout,
        }

        return self._SendRequest("put", ("/%s/instances/%s/shutdown" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def StartupInstance(self, instance, dry_run=False, no_remember=False):
        """
        Starts up an instance.

        @type instance: str
        @param instance: the instance to start up
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        @type no_remember: bool
        @param no_remember: if true, will not record the state change
        @rtype: string
        @return: job id
        """

        query = {
            "dry-run": dry_run,
            "no-remember": no_remember,
        }

        return self._SendRequest("put", ("/%s/instances/%s/startup" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def ReinstallInstance(self, instance, os=None, no_startup=False,
                          osparams=None):
        """
        Reinstalls an instance.

        @type instance: str
        @param instance: The instance to reinstall
        @type os: str or None
        @param os: The operating system to reinstall. If None, the instance's
                current operating system will be installed again
        @type no_startup: bool
        @param no_startup: Whether to start the instance automatically
        """

        if _INST_REINSTALL_REQV1 in self.GetFeatures():
            body = {
                "start": not no_startup,
            }
            if os is not None:
                body["os"] = os
            if osparams is not None:
                body["osparams"] = osparams
            return self._SendRequest("post", ("/%s/instances/%s/reinstall" %
                                              (GANETI_RAPI_VERSION,
                                               instance)), content=body)

        # Use old request format
        if osparams:
            raise GanetiApiError("Server does not support specifying OS"
                                 " parameters for instance reinstallation")

        query = {
            "nostartup": no_startup,
        }

        if os:
            query["os"] = os

        return self._SendRequest("post", ("/%s/instances/%s/reinstall" %
                                          (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def ReplaceInstanceDisks(self, instance, disks=None,
                             mode=REPLACE_DISK_AUTO, remote_node=None,
                             iallocator=None, dry_run=False):
        """
        Replaces disks on an instance.

        @type instance: str
        @param instance: instance whose disks to replace
        @type disks: list of ints
        @param disks: Indexes of disks to replace
        @type mode: str
        @param mode: replacement mode to use (defaults to replace_auto)
        @type remote_node: str or None
        @param remote_node: new secondary node to use (for use with
                replace_new_secondary mode)
        @type iallocator: str or None
        @param iallocator: instance allocator plugin to use (for use with
                                             replace_auto mode)
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "mode": mode,
            "dry-run": dry_run,
        }

        if disks:
            query["disks"] = ",".join(str(idx) for idx in disks)

        if remote_node:
            query["remote_node"] = remote_node

        if iallocator:
            query["iallocator"] = iallocator

        return self._SendRequest("post", ("/%s/instances/%s/replace-disks" %
                                          (GANETI_RAPI_VERSION, instance)),
                                 query=query)

    def PrepareExport(self, instance, mode):
        """
        Prepares an instance for an export.

        @type instance: string
        @param instance: Instance name
        @type mode: string
        @param mode: Export mode
        @rtype: string
        @return: Job ID
        """

        return self._SendRequest("put", ("/%s/instances/%s/prepare-export" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 query={"mode": mode})

    def ExportInstance(self, instance, mode, destination, shutdown=None,
                       remove_instance=None, x509_key_name=None,
                       destination_x509_ca=None):
        """
        Exports an instance.

        @type instance: string
        @param instance: Instance name
        @type mode: string
        @param mode: Export mode
        @rtype: string
        @return: Job ID
        """

        body = {
            "destination": destination,
            "mode": mode,
        }

        if shutdown is not None:
            body["shutdown"] = shutdown

        if remove_instance is not None:
            body["remove_instance"] = remove_instance

        if x509_key_name is not None:
            body["x509_key_name"] = x509_key_name

        if destination_x509_ca is not None:
            body["destination_x509_ca"] = destination_x509_ca

        return self._SendRequest("put", ("/%s/instances/%s/export" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 content=body)

    def MigrateInstance(self, instance, mode=None, cleanup=None):
        """
        Migrates an instance.

        @type instance: string
        @param instance: Instance name
        @type mode: string
        @param mode: Migration mode
        @type cleanup: bool
        @param cleanup: Whether to clean up a previously failed migration
        """

        body = {}

        if mode is not None:
            body["mode"] = mode

        if cleanup is not None:
            body["cleanup"] = cleanup

        return self._SendRequest("put", ("/%s/instances/%s/migrate" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 content=body)

    def FailoverInstance(self, instance, iallocator=None,
                         ignore_consistency=False, target_node=None):
        """Does a failover of an instance.

        @type instance: string
        @param instance: Instance name
        @type iallocator: string
        @param iallocator: Iallocator for deciding the target node for
            shared-storage instances
        @type ignore_consistency: bool
        @param ignore_consistency: Whether to ignore disk consistency
        @type target_node: string
        @param target_node: Target node for shared-storage instances
        @rtype: string
        @return: job id
        """

        body = {
            "ignore_consistency": ignore_consistency,
        }

        if iallocator is not None:
            body["iallocator"] = iallocator
        if target_node is not None:
            body["target_node"] = target_node


        return self._SendRequest("put", ("/%s/instances/%s/failover" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 content=body)

    def RenameInstance(self, instance, new_name, ip_check,
                       name_check=None):
        """
        Changes the name of an instance.

        @type instance: string
        @param instance: Instance name
        @type new_name: string
        @param new_name: New instance name
        @type ip_check: bool
        @param ip_check: Whether to ensure instance's IP address is inactive
        @type name_check: bool
        @param name_check: Whether to ensure instance's name is resolvable
        """

        body = {
            "ip_check": ip_check,
            "new_name": new_name,
        }

        if name_check is not None:
            body["name_check"] = name_check

        return self._SendRequest("put", ("/%s/instances/%s/rename" %
                                         (GANETI_RAPI_VERSION, instance)),
                                 content=body)

    def GetInstanceConsole(self, instance):
        """
        Request information for connecting to instance's console.

        @type instance: string
        @param instance: Instance name
        """

        return self._SendRequest("get", ("/%s/instances/%s/console" %
                                         (GANETI_RAPI_VERSION, instance)))

    def GetJobs(self):
        """
        Gets all jobs for the cluster.

        @rtype: list of int
        @return: job ids for the cluster
        """

        jobs = self._SendRequest("get", "/%s/jobs" % GANETI_RAPI_VERSION)

        return [int(job["id"]) for job in jobs]

    def GetJobStatus(self, job_id):
        """
        Gets the status of a job.

        @type job_id: int
        @param job_id: job id whose status to query

        @rtype: dict
        @return: job status
        """

        return self._SendRequest("get", "/%s/jobs/%s" % (GANETI_RAPI_VERSION,
                                                         job_id))

    def WaitForJobChange(self, job_id, fields, prev_job_info, prev_log_serial):
        """
        Waits for job changes.

        @type job_id: int
        @param job_id: Job ID for which to wait
        """

        body = {
            "fields": fields,
            "previous_job_info": prev_job_info,
            "previous_log_serial": prev_log_serial,
        }

        return self._SendRequest("get", "/%s/jobs/%s/wait" %
                                 (GANETI_RAPI_VERSION, job_id), content=body)

    def CancelJob(self, job_id, dry_run=False):
        """
        Cancels a job.

        @type job_id: int
        @param job_id: id of the job to delete
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        """

        return self._SendRequest("delete", "/%s/jobs/%s" %
                                 (GANETI_RAPI_VERSION, job_id),
                                 query={"dry-run": dry_run})

    def GetNodes(self, bulk=False):
        """
        Gets all nodes in the cluster.

        @type bulk: bool
        @param bulk: whether to return all information about all instances

        @rtype: list of dict or str
        @return: if bulk is true, info about nodes in the cluster,
                else list of nodes in the cluster
        """

        if bulk:
            return self._SendRequest("get", "/%s/nodes" % GANETI_RAPI_VERSION,
                                     query={"bulk": 1})
        else:
            nodes = self._SendRequest("get", "/%s/nodes" %
                                      GANETI_RAPI_VERSION)
            return [n["id"] for n in nodes]

    def GetNode(self, node):
        """
        Gets information about a node.

        @type node: str
        @param node: node whose info to return

        @rtype: dict
        @return: info about the node
        """

        return self._SendRequest("get", "/%s/nodes/%s" % (GANETI_RAPI_VERSION,
                                                          node))

    def EvacuateNode(self, node, iallocator=None, remote_node=None,
                     dry_run=False, early_release=False, mode=None,
                     accept_old=False):
        """
        Evacuates instances from a Ganeti node.

        @type node: str
        @param node: node to evacuate
        @type iallocator: str or None
        @param iallocator: instance allocator to use
        @type remote_node: str
        @param remote_node: node to evaucate to
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        @type early_release: bool
        @param early_release: whether to enable parallelization
        @type accept_old: bool
        @param accept_old: Whether caller is ready to accept old-style
            (pre-2.5) results

        @rtype: string, or a list for pre-2.5 results
        @return: Job ID or, if C{accept_old} is set and server is pre-2.5,
            list of (job ID, instance name, new secondary node); if dry_run
            was specified, then the actual move jobs were not submitted and
            the job IDs will be C{None}

        @raises GanetiApiError: if an iallocator and remote_node are both
                specified
        """

        if iallocator and remote_node:
            raise GanetiApiError("Only one of iallocator or remote_node can"
                                 " be used")

        query = {
            "dry-run": dry_run,
        }

        if iallocator:
            query["iallocator"] = iallocator
        if remote_node:
            query["remote_node"] = remote_node

        if _NODE_EVAC_RES1 in self.GetFeatures():
            # Server supports body parameters
            body = {
                "early_release": early_release,
            }

            if iallocator is not None:
                body["iallocator"] = iallocator
            if remote_node is not None:
                body["remote_node"] = remote_node
            if mode is not None:
                body["mode"] = mode
        else:
            # Pre-2.5 request format
            body = None

            if not accept_old:
                raise GanetiApiError("Server is version 2.4 or earlier and"
                                     " caller does not accept old-style"
                                     " results (parameter accept_old)")

            # Pre-2.5 servers can only evacuate secondaries
            if mode is not None and mode != NODE_EVAC_SEC:
                raise GanetiApiError("Server can only evacuate secondary instances")

            if iallocator is not None:
                query["iallocator"] = iallocator
            if remote_node is not None:
                query["remote_node"] = remote_node
            if query:
                query["early_release"] = 1

        return self._SendRequest("post", ("/%s/nodes/%s/evacuate" %
                                          (GANETI_RAPI_VERSION, node)),
                                 query=query, content=body)

    def MigrateNode(self, node, mode=None, dry_run=False, iallocator=None,
                    target_node=None):
        """
        Migrates all primary instances from a node.

        @type node: str
        @param node: node to migrate
        @type mode: string
        @param mode: if passed, it will overwrite the live migration type,
                otherwise the hypervisor default will be used
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        @type iallocator: string
        @param iallocator: instance allocator to use
        @type target_node: string
        @param target_node: Target node for shared-storage instances

        @rtype: int
        @return: job id
        """

        query = {
            "dry-run": dry_run,
        }

        if _NODE_MIGRATE_REQV1 in self.GetFeatures():
            body = {}

            if mode is not None:
                body["mode"] = mode
            if iallocator is not None:
                body["iallocator"] = iallocator
            if target_node is not None:
                body["target_node"] = target_node

        else:
            # Use old request format
            if target_node is not None:
                raise GanetiApiError("Server does not support specifying"
                                     " target node for node migration")

            body = None

            if mode is not None:
                query["mode"] = mode

        return self._SendRequest("post", ("/%s/nodes/%s/migrate" %
                                          (GANETI_RAPI_VERSION, node)),
                                 query=query, content=body)

    def GetNodeRole(self, node):
        """
        Gets the current role for a node.

        @type node: str
        @param node: node whose role to return

        @rtype: str
        @return: the current role for a node
        """

        return self._SendRequest("get", ("/%s/nodes/%s/role" %
                                         (GANETI_RAPI_VERSION, node)))

    def SetNodeRole(self, node, role, force=False, auto_promote=False):
        """
        Sets the role for a node.

        @type node: str
        @param node: the node whose role to set
        @type role: str
        @param role: the role to set for the node
        @type force: bool
        @param force: whether to force the role change
        @type auto_promote: bool
        @param auto_promote: Whether node(s) should be promoted to master
            candidate if necessary

        @rtype: int
        @return: job id
        """

        query = {
            "force": force,
            "auto_promote": auto_promote,
        }

        return self._SendRequest("put", ("/%s/nodes/%s/role" %
                                         (GANETI_RAPI_VERSION, node)),
                                 query=query, content=role)

    def PowercycleNode(self, node, force=False):
        """
        Powercycles a node.

        @type node: string
        @param node: Node name
        @type force: bool
        @param force: Whether to force the operation
        @rtype: string
        @return: job id
        """

        query = {
            "force": force,
        }

        return self._SendRequest("post", ("/%s/nodes/%s/powercycle" %
                                          (GANETI_RAPI_VERSION, node)),
                                 query=query)

    def ModifyNode(self, node, **kwargs):
        """
        Modifies a node.

        More details for parameters can be found in the RAPI documentation.

        @type node: string
        @param node: Node name
        @rtype: string
        @return: job id
        """

        return self._SendRequest("post", ("/%s/nodes/%s/modify" %
                                          (GANETI_RAPI_VERSION, node)),
                                 content=kwargs)

    def GetNodeStorageUnits(self, node, storage_type, output_fields):
        """
        Gets the storage units for a node.

        @type node: str
        @param node: the node whose storage units to return
        @type storage_type: str
        @param storage_type: storage type whose units to return
        @type output_fields: str
        @param output_fields: storage type fields to return

        @rtype: int
        @return: job id where results can be retrieved
        """

        query = {
            "storage_type": storage_type,
            "output_fields": output_fields,
        }

        return self._SendRequest("get", ("/%s/nodes/%s/storage" %
                                         (GANETI_RAPI_VERSION, node)),
                                 query=query)

    def ModifyNodeStorageUnits(self, node, storage_type, name,
                               allocatable=None):
        """
        Modifies parameters of storage units on the node.

        @type node: str
        @param node: node whose storage units to modify
        @type storage_type: str
        @param storage_type: storage type whose units to modify
        @type name: str
        @param name: name of the storage unit
        @type allocatable: bool or None
        @param allocatable: Whether to set the "allocatable" flag on the storage
                                                unit (None=no modification, True=set, False=unset)

        @rtype: int
        @return: job id
        """

        query = {
            "storage_type": storage_type,
            "name": name,
        }

        if allocatable is not None:
            query["allocatable"] = allocatable

        return self._SendRequest("put", ("/%s/nodes/%s/storage/modify" %
                                         (GANETI_RAPI_VERSION, node)),
                                 query=query)

    def RepairNodeStorageUnits(self, node, storage_type, name):
        """
        Repairs a storage unit on the node.

        @type node: str
        @param node: node whose storage units to repair
        @type storage_type: str
        @param storage_type: storage type to repair
        @type name: str
        @param name: name of the storage unit to repair

        @rtype: int
        @return: job id
        """

        query = {
            "storage_type": storage_type,
            "name": name,
        }

        return self._SendRequest("put", ("/%s/nodes/%s/storage/repair" %
                                         (GANETI_RAPI_VERSION, node)),
                                 query=query)

    def GetNodeTags(self, node):
        """
        Gets the tags for a node.

        @type node: str
        @param node: node whose tags to return

        @rtype: list of str
        @return: tags for the node
        """

        return self._SendRequest("get", ("/%s/nodes/%s/tags" %
                                         (GANETI_RAPI_VERSION, node)))

    def AddNodeTags(self, node, tags, dry_run=False):
        """
        Adds tags to a node.

        @type node: str
        @param node: node to add tags to
        @type tags: list of str
        @param tags: tags to add to the node
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "tag": tags,
            "dry-run": dry_run,
        }

        return self._SendRequest("put", ("/%s/nodes/%s/tags" %
                                         (GANETI_RAPI_VERSION, node)),
                                 query=query, content=tags)

    def DeleteNodeTags(self, node, tags, dry_run=False):
        """
        Delete tags from a node.

        @type node: str
        @param node: node to remove tags from
        @type tags: list of str
        @param tags: tags to remove from the node
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "tag": tags,
            "dry-run": dry_run,
        }

        return self._SendRequest("delete", ("/%s/nodes/%s/tags" %
                                            (GANETI_RAPI_VERSION, node)),
                                 query=query)

    def GetGroups(self, bulk=False):
        """
        Gets all node groups in the cluster.

        @type bulk: bool
        @param bulk: whether to return all information about the groups

        @rtype: list of dict or str
        @return: if bulk is true, a list of dictionaries with info about all node
                groups in the cluster, else a list of names of those node groups
        """

        if bulk:
            return self._SendRequest("get", "/%s/groups" %
                                     GANETI_RAPI_VERSION, query={"bulk": 1})
        else:
            groups = self._SendRequest("get", "/%s/groups" %
                                       GANETI_RAPI_VERSION)
            return [g["name"] for g in groups]

    def GetGroup(self, group):
        """
        Gets information about a node group.

        @type group: str
        @param group: name of the node group whose info to return

        @rtype: dict
        @return: info about the node group
        """

        return self._SendRequest("get", "/%s/groups/%s" %
                                 (GANETI_RAPI_VERSION, group))

    def CreateGroup(self, name, alloc_policy=None, dry_run=False):
        """
        Creates a new node group.

        @type name: str
        @param name: the name of node group to create
        @type alloc_policy: str
        @param alloc_policy: the desired allocation policy for the group, if any
        @type dry_run: bool
        @param dry_run: whether to peform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "dry-run": dry_run,
        }

        body = {
            "name": name,
            "alloc_policy": alloc_policy
        }

        return self._SendRequest("post", "/%s/groups" % GANETI_RAPI_VERSION,
                                 query=query, content=body)

    def ModifyGroup(self, group, **kwargs):
        """
        Modifies a node group.

        More details for parameters can be found in the RAPI documentation.

        @type group: string
        @param group: Node group name
        @rtype: int
        @return: job id
        """

        return self._SendRequest("put", ("/%s/groups/%s/modify" %
                                         (GANETI_RAPI_VERSION, group)),
                                 content=kwargs)

    def DeleteGroup(self, group, dry_run=False):
        """
        Deletes a node group.

        @type group: str
        @param group: the node group to delete
        @type dry_run: bool
        @param dry_run: whether to peform a dry run

        @rtype: int
        @return: job id
        """

        query = {
            "dry-run": dry_run,
        }

        return self._SendRequest("delete", ("/%s/groups/%s" %
                                            (GANETI_RAPI_VERSION, group)),
                                 query=query)

    def RenameGroup(self, group, new_name):
        """
        Changes the name of a node group.

        @type group: string
        @param group: Node group name
        @type new_name: string
        @param new_name: New node group name

        @rtype: int
        @return: job id
        """

        body = {
            "new_name": new_name,
        }

        return self._SendRequest("put", ("/%s/groups/%s/rename" %
                                         (GANETI_RAPI_VERSION, group)),
                                 content=body)


    def AssignGroupNodes(self, group, nodes, force=False, dry_run=False):
        """
        Assigns nodes to a group.

        @type group: string
        @param group: Node gropu name
        @type nodes: list of strings
        @param nodes: List of nodes to assign to the group

        @rtype: int
        @return: job id

        """

        query = {
            "force": force,
            "dry-run": dry_run,
        }

        body = {
            "nodes": nodes,
        }

        return self._SendRequest("put", ("/%s/groups/%s/assign-nodes" %
                                         (GANETI_RAPI_VERSION, group)),
                                 query=query, content=body)

    def GetGroupTags(self, group):
        """
        Gets tags for a node group.

        @type group: string
        @param group: Node group whose tags to return

        @rtype: list of strings
        @return: tags for the group
        """

        return self._SendRequest("get", ("/%s/groups/%s/tags" %
                                         (GANETI_RAPI_VERSION, group)))

    def AddGroupTags(self, group, tags, dry_run=False):
        """
        Adds tags to a node group.

        @type group: str
        @param group: group to add tags to
        @type tags: list of string
        @param tags: tags to add to the group
        @type dry_run: bool
        @param dry_run: whether to perform a dry run

        @rtype: string
        @return: job id
        """

        query = {
            "dry-run": dry_run,
            "tag": tags,
        }

        return self._SendRequest("put", ("/%s/groups/%s/tags" %
                                         (GANETI_RAPI_VERSION, group)),
                                 query=query)

    def DeleteGroupTags(self, group, tags, dry_run=False):
        """
        Deletes tags from a node group.

        @type group: str
        @param group: group to delete tags from
        @type tags: list of string
        @param tags: tags to delete
        @type dry_run: bool
        @param dry_run: whether to perform a dry run
        @rtype: string
        @return: job id
        """

        query = {
            "dry-run": dry_run,
            "tag": tags,
        }

        return self._SendRequest("delete", ("/%s/groups/%s/tags" %
                                            (GANETI_RAPI_VERSION, group)),
                                 query=query)

    def Query(self, what, fields, qfilter=None):
        """
        Retrieves information about resources.

        @type what: string
        @param what: Resource name, one of L{constants.QR_VIA_RAPI}
        @type fields: list of string
        @param fields: Requested fields
        @type qfilter: None or list
        @param qfilter: Query filter

        @rtype: string
        @return: job id
        """

        body = {
            "fields": fields,
        }

        if qfilter is not None:
            body["qfilter"] = body["filter"] = qfilter

        return self._SendRequest("put", ("/%s/query/%s" %
                                         (GANETI_RAPI_VERSION, what)),
                                 content=body)

    def QueryFields(self, what, fields=None):
        """
        Retrieves available fields for a resource.

        @type what: string
        @param what: Resource name, one of L{constants.QR_VIA_RAPI}
        @type fields: list of string
        @param fields: Requested fields

        @rtype: string
        @return: job id
        """

        query = {}

        if fields is not None:
            query["fields"] = ",".join(fields)

        return self._SendRequest("get", ("/%s/query/%s/fields" %
                                         (GANETI_RAPI_VERSION, what)),
                                 query=query)
