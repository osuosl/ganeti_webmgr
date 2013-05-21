Importing a Cluster
===================

#. Log in as an admin user.
#. Navigate *Clusters -> Add Cluster*
#. Fill out properties and click *save*

When the Cluster is imported into Ganeti Web Manager it will
automatically synchronize. Virtual Machine objects will be created to
match what is found on the Ganeti Cluster. :ref:`permission-tags` will
also be parsed to automatically add permissions for virtual machines.

Note that if the cluster requires a username and password, you must
enter these in order to modify the cluster through the web manager. If
you leave the fields blank or enter incorrect credentials, you will be
able to view the cluster's virtual machines but there will be errors if
you try to modify them or create new ones. You can edit the cluster's
properties by using the "edit" button on the cluster detail page. The
edit button will only be visible if you're logged in as a cluster admin
or superuser.

:ref:`permissions` can be or you can use the :ref:`orphans` tool to find
virtual machines with no permissions.

