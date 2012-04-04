"""
Class for connecting the raw RAPI client with higher-level logical operations
on objects.
"""

from django.conf import settings

from object_log.models import LogItem
log_action = LogItem.objects.log_action

from ganeti_web.models import Job
from ganeti_web.util.client import REPLACE_DISK_AUTO, GanetiRapiClient

class RAPI(object):
    """
    A high-level connector for operations on a Ganeti RAPI resource.
    """

    def __init__(self, cluster):
        self.cluster = cluster
        self._client = GanetiRapiClient(cluster.hostname, cluster.port,
                                        cluster.username, cluster.password,
                                        timeout=settings.RAPI_CONNECT_TIMEOUT)

    def _attach_job(self, obj, jid):
        """
        Attach a job to a VM.
        """

        job = Job.objects.create(job_id=jid, obj=obj, cluster_id=obj.cluster_id)
        job.refresh()
        obj.last_job = job
        obj.ignore_cache = True
        obj.save()

        return job

    def startup(self, vm, user):
        """
        Start a VM.
        """

        jid = int(self._client.StartupInstance(vm.hostname))
        job = self._attach_vm_job(vm, jid)
        log_action('VM_START', user, vm, job)
        return job

    def reboot(self, vm, user):
        """
        Politely restart a VM.
        """

        jid = int(self._client.RebootInstance(vm.hostname))
        job = self._attach_vm_job(vm, jid)
        log_action('VM_REBOOT', user, vm, job)
        return job

    def shutdown(self, vm, user, timeout=None):
        """
        Halt a VM.
        """

        if timeout is None:
            jid = self._client.ShutdownInstance(self.hostname)
        else:
            jid = self._client.ShutdownInstance(self.hostname,
                                                timeout=timeout)

        jid = int(jid)
        job = self._attach_vm_job(vm, jid)
        log_action('VM_STOP', user, vm, job)
        return job

    def rename(self, vm, name, user, ip_check=None, name_check=None):
        """
        Rename a VM.

        If the VM is running, it will be shut down first.
        """

        # VMs must be shut down in order to be renamed.
        if vm.is_running:
            job = self.shutdown(vm, user)

        jid = self._client.RenameInstance(vm.hostname, name,
                                          ip_check=ip_check,
                                          name_check=name_check)

        # Slip the new hostname to the log before setting the new name and
        # running the rename job.
        vm.newname = name
        log_action('VM_RENAME', user, vm, job)
        vm.hostname = name
        job = self._attach_vm_job(vm, jid)
        return job

    def migrate_vm(self, vm, user, mode='live', cleanup=False):
        """
        Migrate a VM to another node.

        The VM's disk type must be DRDB.
        """

        jid = self._client.MigrateInstance(vm.hostname, mode, cleanup)
        job = self._attach_vm_job(vm, jid)
        log_action('VM_MIGRATE', user, vm, job)
        return job

    def replace_disks(self, vm, user, mode=REPLACE_DISK_AUTO, disks=None,
                      node=None, iallocator=None):
        """
        Replace the disks in a VM.
        """

        jid = self._client.ReplaceInstanceDisks(vm.hostname, disks, mode,
                                                node, iallocator)
        job = self._attach_vm_job(vm, jid)
        log_action('VM_REPLACE_DISKS', user, vm, job)
        return job

    def set_role(self, node, user, role, force=False):
        """
        Set the role for a node.

        Roles may be one of: master, master-candidate, regular, drained,
        offline.
        """

        jid = self._client.SetNodeRole(node.hostname, role, force)
        job = self._attach_job(node, jid)
        log_action('NODE_ROLE_CHANGE', user, node)
        return job

    def evacuate(self, node, user, iallocator=None, remote_node=None):
        """
        Migrate all secondary instances off of a node.
        """

        jid = self._client.EvacuateNode(node.hostname, iallocator=iallocator,
                                       remote_node=remote_node)
        job = self._attach_job(node, jid)
        log_action('NODE_EVACUATE', user, node, job)
        return job

    def migrate_node(self, node, user, mode=None):
        """
        Migrate all primary instances off of a node.
        """

        jid = self._client.MigrateNode(node.hostname, mode)
        job = self._attach_job(node, jid)
        log_action('NODE_MIGRATE', user, node)
        return job
