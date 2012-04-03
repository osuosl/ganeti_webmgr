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

    def shutdown(self, vm):
        """
        Halt a VM.
        """

        jid = int(self._client.ShutdownInstance(vm.hostname))
        job = Job.objects.create(job_id=jid, obj=vm, cluster_id=vm.cluster_id)
        job.refresh()
        vm.last_job = job
        vm.ignore_cache = True
        vm.save()

        return job
