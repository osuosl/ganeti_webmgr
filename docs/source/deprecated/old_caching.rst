.. _old_caching:

Deprecated: Caching
===================

.. warning::
  This document is deprecated as of |gwm| version 0.11.

.. figure:: /_static/ganeti_cache.png
   :align: center

Ganeti Web Manager uses a cache system that stores information about
ganeti clusters in the database. This allows the following:

-  Permissions are stored in the database and are associated to the
   cached objects
-  The cached data can be searched and or filtered
-  Limits the amount of traffic between the webserver and ganeti
   cluster.

The cache system is transparent and will load cached data automatically
when the object is initialized.

.. _lazy-cache:

Lazy Cache Refresh
------------------

Cached objects will refresh themselves transparently when they are out
of date. This happens transparently when objects are queried from the
ORM. Lazy cache refreshing is inefficient, it will cause multiple calls
to the ganeti RAPI to fetch information. For this reason the lazy
refresh mechanism is intended to only be used for testing, and as a
backup to ensure that objects will always be refreshed.


.. _periodic-cache-updater:

CachedClusterObject
-------------------

The functionality for lazy caching is built into an abstract model,
CachedClusterObject. Extending this model will enable caching for the
object. It requires that **\_refresh()** be implemented with an object
specific method for querying fresh info from ganeti. Currently only
Cluster and VirtualMachine are cached, but this may extend to Node and
Job objects in the future.

**parse\_persistent\_info()** can be overridden to parse object specific
properties that should be stored in the database. This allows properties
to be used as query filters, without requiring the entire object to be
loaded.

Bypassing The Cache Refresh
~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is not currently possible to bypass the automatic cache refresh in a
simple way since it is part of the models ***init***. Currently the only
way to bypass the cache is to query the object with a values or
values\_list query, and copy the values into a new object.

::

    values = VirtualMachine.objects.get(id=id)
    vm = VirtualMachine()
    for k, v in values.items():
        setattr(vm, k , v)

RAPI Client Cache
-----------------

Ganeti remote API clients are also cached. This reduces the number of
database calls to retrieve a client capable of connecting to a cluster.
This is a deterministic cache based off connection credentials. The keys
are a hash of hostname, port, user, and password. This allows changes in
settings to be easily detected. Cached objects should store the hash as
part of its model and use it to look up existing clients without
querying the cluster for the full set of connection credentials.
