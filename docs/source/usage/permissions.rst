Permissions
===========

Permissions may be granted to both clusters and virtual machines. The
permissions system is intended to allow users to manage themselves. Any
object that can have its permissions edited will have a *Users* tab.

For a high level description of how permissions can be used in various
scenarios, read this `blog
post <http://blogs.osuosl.org/kreneskyp/2010/12/28/ganeti-web-manager-permissions/>`_.

Contents

-  `Permissions <#Permissions>`_

   -  

      -  `Adding users to objects. <#Adding-users-to-objects>`_
      -  `Updating permissions <#Updating-permissions>`_
      -  `Deleting permissions <#Deleting-permissions>`_

   -  `Groups <#Groups>`_

      -  `Group Permissions <#Group-Permissions>`_

   -  `Cluster <#Cluster>`_
   -  `Quotas <#Quotas>`_
   -  `Virtual Machines <#Virtual-Machines>`_

      -  `Permission Tags <#Permission-Tags>`_

Adding users to objects.
~~~~~~~~~~~~~~~~~~~~~~~~

#. navigate to Group, Cluster, or VirtualMachine detail page
#. click *Add New User*
#. select user or group
#. select permissions
#. *save*

Updating permissions
~~~~~~~~~~~~~~~~~~~~

#. navigate to Group, Cluster, or VirtualMachine detail page
#. click *Users* tab
#. click permissions column
#. select permissions and *save*

Deleting permissions
~~~~~~~~~~~~~~~~~~~~

#. navigate to Group, Cluster, or VirtualMachine detail page
#. click *Users* tab
#. click the *delete* icon

Deleting a user will remove all permissions, and other properties
associated with the user such as cluster quotas.

Groups
------

Groups may be created so that permissions. This allows permissions
structures where you are granting permissions to different
organizations. Users may belong to unlimited number of groups. They will
inherit the permissions of any group they belong to.

Groups are a persona that user's may act on behalf of. When creating
virtual machines, the user must choose whether they are acting on behalf
of themselves or a group they are a member of. When acting on behalf of
a group, the group's permissions and quota used.

Group Permissions
~~~~~~~~~~~~~~~~~

-  **admin** - Grants the ability to see the member list, and edit
   permissions

Cluster
-------

These permissions can be granted to either a user or a group. A user who
is part of a group with a permission does not automatically have that
permission individually. For instance, a user who is part of a group
that has VM create permission can create a VM, but can only assign
ownership to the group, not to themself. To grant permissions on a
cluster, click *add user* on the Users tab of the cluster detail page.
Cluster permissions can also be added by clicking *Add Cluster* in the
Permissions tab of the user detail page.

-  **admin** - Grants full access to the cluster. Includes ability to
   set permissions and quotas, and full access to all virtual machines.
-  **create\_vm** - Grants ability to create virtual machines on the
   cluster.
-  **tags** - Grants ability to set tags on the cluster.
-  **replace disks** - Ability to replace disks of VMs on the cluster.
-  **migrate** - Can migrate a VM to another node
-  **export** - Can export a virtual machine

Quotas
------

Quotas restrict the usage of cluster resources by users and groups.
Default quotas can be set by editing clusters, if no quota is set
unlimited access is allowed. This will affect all users and groups.

The default quota can be overridden on the cluster users page:

#. *Clusters -> Cluster -> Users*
#. click quota value.
#. edit values, and click *save*

Leaving a value empty specifies unlimited access for that resource.

Virtual Machines
----------------

To grant a user permissions on a VM, click *Add VirtualMachine* in the
Permissions tab of the User detail page. To grant permissions to a user
or group, use the *Add User* button on the Users tab of the VM detail
page.

-  **admin** - Grants full access to the virtual machine, including
   granting permissions.
-  **Modify** - Allows user to modify VM's settings, including
   reinstallation of OS
-  **Remove** - Permission to delete this VM
-  **Power** - Permission to start, stop, reboot, and access console
-  **Tags** - Can set tags for this VM

Permission Tags
~~~~~~~~~~~~~~~

Permissions for virtual machines are also registered as tags on the
virtual machine object. This allows the permissions to be viewed and set
via the command line tool. Tags will be parsed when creating virtual
machines, and will be updated when the object is refreshed
(`#387 </issues/387>`_). When permissions are granted tags will be set
on the virtual machine (`#393 </issues/393>`_).

Tags use the pattern:
*GANETI\_WEB\_MANAGER:<permission>:[G\|U]:<user\_id>*

-  **GANETI\_WEB\_MANAGER:admin:U:2** - admin permission for User with
   id 2
-  **GANETI\_WEB\_MANAGER:admin:G:4** - admin permission for Group with
   id 4
-  **GANETI\_WEB\_MANAGER:start:U:2** - start permission for User with
   id 2
