Cluster Read Only Mode
======================

It is possible to add a cluster with only its hostname and port number,
and no username and password credentials. This creates a copy of the
cluster and its VMs in your local Ganeti Web Manager database without
giving you the ability to change the cluster itself.

In Read-Only mode, you CAN:
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Assign ownership of VMs to GWM users from the Orphans page
-  Delete VMs from your Ganeti Webmanager database from the Missing VMs
   page
-  Import nodes to your database or delete nodes from it
-  Assign permissions to users on the cluster or VM (note that although
   you can assign VM create permission to a user or group, they cannot
   actually create a VM in read-only mode)
-  Edit the cluster, so that you can go back and add username/password
   credentials and gain full privileges on it later.
-  Delete the record of the cluster from your database (Note: This does
   not affect the actual cluster)
-  Record a default quotas for Virtual CPUs, Disk Space, and Memory
-  Change the cluster's slug (the name of the cluster as it appears in
   the url: <hostname>/cluster/<slug>/<vm>)

In Read-Only mode, you can NOT:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Redistribute the cluster's configuration
-  Start, stop, or reinstall a VM
-  Migrate or change disks
-  Access a VM's console
-  Create a new VM on the cluster

