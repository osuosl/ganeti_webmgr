from django.core.management.base import NoArgsCommand
from clusters.models import Cluster
from nodes.models import Node
from virtualmachines.models import VirtualMachine

from utils.client import GanetiApiError


class Command(NoArgsCommand):
    help = "Refreshes the Cache for Clusters, Nodes and Virtual Machines."

    def handle_noargs(self, **options):
        self.refresh_objects(**options)

    def refresh_objects(self, **options):
        """
        This was originally the code in the 0009
        and then 0010 'force_object_refresh' migration

        Force a refresh of all Cluster, Nodes, and VirtualMachines, and
        import any new Nodes.
        """
        write = self.stdout.write
        flush = self.stdout.flush

        def wf(str, newline=False, verbosity=1):
            if (verbosity > 0):
                if newline:
                    write('\n')
                write(str)
                flush()

        verbosity = int(options.get('verbosity'))

        wf('- Refreshing Cached Cluster Objects', verbosity=verbosity)

        wf('> Synchronizing Cluster Nodes ', True, verbosity=verbosity)
        flush()
        Cluster.objects.all().update(mtime=None)
        for cluster in Cluster.objects.all().iterator():
            try:
                cluster.sync_nodes()
                wf('.', verbosity=verbosity)
            except GanetiApiError:
                wf('E', verbosity=verbosity)

        Node.objects.all().update(mtime=None)
        wf('> Refreshing Node Caches ', True, verbosity=verbosity)
        for node in Node.objects.all().iterator():
            try:
                wf('.', verbosity=verbosity)
            except GanetiApiError:
                wf('E', verbosity=verbosity)

        VirtualMachine.objects.all().update(mtime=None)
        wf('> Refreshing Instance Caches ', True, verbosity=verbosity)
        for instance in VirtualMachine.objects.all().iterator():
            try:
                wf('.', verbosity=verbosity)
            except GanetiApiError:
                    wf('E', verbosity=verbosity)

        wf('\n', verbosity=verbosity)
