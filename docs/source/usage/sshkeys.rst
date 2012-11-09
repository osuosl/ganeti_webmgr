SSHKeys
=======

Ganeti Web Manager allows users to store SSH Keys. Each virtual machine
has a view that will return SSH keys for users with access.

Configuring User SSH Keys
-------------------------

As an User
~~~~~~~~~~

#. click your **username** in the menu sidebar
#. use the Add, Edit, and Delete buttons to manage your keys

As an Admin
~~~~~~~~~~~

#. click **Users** in the menu sidebar
#. click the edit button for the user you want to edit
#. use the Add, Edit, and Delete buttons to manage your keys

SSH Keys script
---------------

Ganeti Web Manager provides a script that will automatically generate an
authorized\_keys files

::

    python util/sshkeys.py [-c CLUSTER [-i INSTANCE]] API_KEY URL

-  **API\_KEY** is the value set in **settings.py**
-  **URL** is a URL pointing to the GWM server
-  **CLUSTER** is the identifier of a cluster
-  **INSTANCE** is the hostname of an instance

The GWM server URL has some flexibility in how it may be specified; HTTP
and HTTPS are supported, as well as custom port numbers. The following
are all valid URLs:

-  `http://example.com/ <http://example.com/>`_
-  `https://example.com/ <https://example.com/>`_
-  `http://example.com:8080/ <http://example.com:8080/>`_

**CLUSTER** and **INSTANCE** are optional. Including them will narrow
the list of users to either a **Cluster** or a **VirtualMachine**.

SSH Keys Ganeti hook
--------------------

If you want your VMs to automatically copy the ssh keys from GWM, then
you can use the included ssh keys ganeti hook found in
**``util/hooks/sshkeys.sh``**. Copy that file onto every node in your
cluster in the hooks directory for the instance definition you're using
(i.e. ganeti-debootstrap). Copy and set the variables in
**``util/hooks/sshkeys.conf``** into the variant config and/or the
instance definition config file. Make sure that the hook is executable
and all the variables are set include changing the API Key.
