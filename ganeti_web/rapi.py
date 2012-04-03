"""
Class for connecting the raw RAPI client with higher-level logical operations
on objects.
"""

from django.conf import settings

from ganeti_web.models import Job
from ganeti_web.util.client import GanetiRapiClient

class RAPI(object):
    """
    A high-level connector for operations on a Ganeti RAPI resource.
    """

    def __init__(self, cluster):
        self.cluster = cluster
        self._client = GanetiRapiClient(cluster.hostname, cluster.port,
                                        cluster.username, cluster.password,
                                        timeout=settings.RAPI_CONNECT_TIMEOUT)

    def _attach_vm_job(self, vm, jid):
        """
        Attach a job to a VM.
        """

        job = Job.objects.create(job_id=jid, obj=vm, cluster_id=vm.cluster_id)
        job.refresh()
        vm.last_job = job
        vm.ignore_cache = True
        vm.save()

        return job

    def startup(self, vm):
        """
        Start a VM.
        """

        jid = int(self._client.StartupInstance(vm.hostname))
        return self._attach_vm_job(vm, jid)

    def reboot(self, vm):
        """
        Politely restart a VM.
        """

        jid = int(self._client.RebootInstance(vm.hostname))
        return self._attach_vm_job(vm, jid)

    def shutdown(self, vm, timeout=None):
        """
        Halt a VM.
        """

        if timeout is None:
            jid = self._client.ShutdownInstance(self.hostname)
        else:
            jid = self._client.ShutdownInstance(self.hostname,
                                                timeout=timeout)

        jid = int(jid)
        return self._attach_vm_job(vm, jid)
