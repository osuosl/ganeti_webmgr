=======
Caching
=======

Ganeti Web Manager caches objects for performance reasons.

Why are things cached?
======================

Ganeti is a bottleneck when accessing data. In tests, over 97% of time taken
to render a normal page in Ganeti Web Manager is spent waiting for Ganeti to
respond to queries. Thus, Ganeti Web Manager caches some of Ganeti's data.

Manual Updates
==============

Sometimes it is necessary to refresh objects manually. To do this, navigate to
the detail page for the cluster of the object that needs to be refreshed, and
click the "Refresh" button. This will refresh the cluster and all of its
objects.

Cached Cluster Objects
======================

Some database-bound objects cache Ganeti data automatically. The functionality
for this caching is encapsulated in the ``CachedClusterObject`` class. Any
models which inherit from this class will gain this functionality.

Bypassing the Cache
-------------------

The cache cannot currently be bypassed reasonably. ``CachedClusterObject``
uses ``__init__()`` to do part of its work. An unreasonable, albeit working,
technique is to abuse the ORM::

    values = VirtualMachine.objects.get(id=id)
    vm = VirtualMachine()
    for k, v in values.items():
        setattr(vm, k, v)

RAPI Cache
==========

RAPI clients are cached in memory, and a hash of cluster information is stored
in order to locate them quickly. The entire scheme is no longer necessary
since RAPI clients are no longer expensive to allocate, and will be removed
soon.
