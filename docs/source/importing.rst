Importing a Cluster
===================

#. Log in as an admin user.
#. Navigate *Clusters -> Add Cluster*
#. Fill out properties and click *save*

When the Cluster is imported into Ganeti Web Manager it will
automatically synchronize. Virtual Machine objects will be created to
match what is found on the Ganeti Cluster. `Permission
tags </projects/ganeti-webmgr/wiki/Permissions#Permission-Tags>`_ will
also be parsed to automatically add permissions for virtual machines.

Note that if the cluster requires a username and password, you must
enter these in order to modify the cluster through the web manager. If
you leave the fields blank or enter incorrect credentials, you will be
able to view the cluster's virtual machines but there will be errors if
you try to modify them or create new ones. You can edit the cluster's
properties by using the "edit" button on the cluster detail page. The
edit button will only be visible if you're logged in as a cluster admin
or superuser.

Permissions can be `edited
manually </projects/ganeti-webmgr/wiki/Permissions>`_ or you can use the
`orphans
tool </projects/ganeti-webmgr/wiki/Managing_Clusters#Orphaned-Virtual-Machines>`_
to find virtual machines with no permissions.
