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
