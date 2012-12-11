Managing Clusters
=================

Ganeti RAPI users and passwords
-------------------------------

Before you can start using Ganeti Web Manager you will need to create a
user and password on the Ganeti cluster.

Create MD5 hash
~~~~~~~~~~~~~~~

Here is an example with a user **jack** and password **abc123**

::

    echo -n 'jack:Ganeti Remote API:abc123' | openssl md5

Add user to Ganeti cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the hash to ``/var/lib/ganeti/rapi_users`` on all the nodes in the
cluster and restart ganeti-rapi. Here's an example using above:
For ganeti 2.4 and above you need use file /var/lib/ganeti/rapi/users

::

    # Hashed password for jack
    jack {HA1}54c12257ee9be413f2f3182435514aae write

For more information on adding users, please check the `Ganeti RAPI
documentation <http://docs.ganeti.org/ganeti/current/html/rapi.html#users-and-passwords>`_

Adding a Cluster
----------------

#. Log in as an admin user.
#. Navigate *Clusters -> Add Cluster*
#. Fill out properties and click *save*

When the Cluster is added it will automatically synchronize. Virtual
Machines objects will be created to match what is found on the Ganeti
Cluster. :ref:`permission-tags` will
also be parsed to automatically add permissions for virtual machines.

A cluster can be added with only its hostname and port, but a username
and password for the cluster are required if you want to make changes to
it. Clusters added without a valid username and password appear in
:doc:`cluster-read-only` where you can only change aspects of the
cluster that are local to Ganeti Web Manager's database.

:doc:`permissions` can be edited manually or you can use the
:ref:`orphans` tool to find virtual machines with no
permissions.

Synchronizing Clusters
----------------------

Ganeti Web Manager stores some information about clusters in its
database. Cluster and virtual machine information will
:ref:`refresh automatically <lazy-cache>`, but the list of virtual
machines must be synchronized manually. This can be done by via the
orphans view

#. Main Menu -> Orphans

Clusters are synchronized when the orphans view is visited.

Adding Virtual Machines
-----------------------

To add a virtual machine, select "Create VM" in the toolbar. Only fields
with multiple options will be selectable. For example, if you are unable
to change the cluster to which a VM gets added, it means that there is
only one valid option and cluster is a mandatory field.

-  If the user creating the VM has permissions to do so, the owner will
   be that user. If the user does not have create permissions but is a
   member of a group that can create VMs, ownership defaults to that
   group.
-  Cluster can be chosen from those that the the user creating the VM
   has access to.
-  The Hypervisor will generally be dictated by the cluster that you
   choose.
-  The instance name must be a fully qualified domain name (FQDN). (e.g.
   hostname.example.org)
-  If you uncheck "Start up after creation", you can start the VM
   manually on its virtual machine detail page. (click Virtual Machines
   in the sidebar, then the VM's name)
-  DNS name check: if checked, sends the name you selected for the VM to
   the resolver (e.g. in DNS or /etc/hosts, depending on your setup).
   Since the name check is used to compute the IP address this also
   enables/disables IP checks (e.g. if the IP is pingable). Uncheck if
   using dynamic DNS.
-  Disk Template chooses a layout template from these options:

   -  plain - Disk devices will be logical volumes (e.g. LVM)
   -  drbd - Disk devices will be DRBD (version8.x) on top of LVM
      volumes

      -  If drbd is selected, a primary and secondary node will need to
         be chosen unless automatic allocation has been selection. DRBD
         will allow the virtual machine to use live migration and
         failover in case one of the nodes goes offline.

   -  file - Disk devices will be regular files (e.g. qcow2)
   -  diskless - This creates a virtual machine with no disks. Its
      useful for testing only (or other special cases).

-  Operating system to install on the virtual machine. Your choices are
   limited to the images configured on the cluster.

General Parameters:

-  Virtual CPUs will be deducted from owner's quota. If the owner field
   appears blank and is not selectable, the default owner has been
   chosen.
-  Memory is the amount of RAM to give this VM. If no units are given,
   megabytes is assumed.
-  Disk size is the amount of owner's disk quota to allot this VM. If no
   units are given, megabytes is assumed.
-  Disk type determines the way the disks are presented to the virtual
   machine. Options may vary based on cluster's hypervisor settings.
-  More information about NIC Mode, NIC Link, and NIC Type can be found
   `here <http://docs.ganeti.org/ganeti/current/html/install.html#configuring-the-network>`_

Hypervisor parameters:

*TODO finish this part*

.. _orphans:

Orphaned Virtual Machines
-------------------------

:ref:`permission-tags` are parsed by virtual machine objects, but
sometimes virtual machines will have no tags. To quickly identify
virtual machines with no admin users, use the orphans view

#. Main Menu -> Orphans

Visiting the orphans view will force a synchronization of all clusters
and display VirtualMachines that do not have any permissions assigned.
You only need to grant permissions directly on virtual machines if you
are granting access to non-admin users.
