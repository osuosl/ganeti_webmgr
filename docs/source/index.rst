.. Ganeti Web Manager documentation master file, created by
   sphinx-quickstart on Fri Oct 26 11:40:24 2012.

Ganeti Web Manager
==================

|gwm| is a Django_ based web frontend for managing Ganeti_ virtualization
clusters. Since Ganeti only provides a command-line interface, |gwm|'s
goal is to provide a user friendly interface to Ganeti by being feature
complete with Ganeti's :ref:`RAPI <rapi>`. On top of Ganeti it
provides a permission system for managing access to clusters and virtual
machines and an in browser VNC console.

If you don't already have a Ganeti cluster setup, these directions_ can
help you get started. If you are looking for support, please contact us
through these :ref:`channels <contact>`. If you are looking to deploy
|gwm| for the first time, check out our :ref:`installation` guide. If
you already have a |gwm| instance running it might be time to
:ref:`upgrade <upgrading>`.


|gwm| is licensed under the :ref:`GPLv2 <license>`. It is currently
developed and maintained by the Oregon State University Open Source Lab
and a handful of volunteers. If you would like to get involved in
development see our :ref:`development <development>` guide.


.. _directions: http://docs.ganeti.org/ganeti/current/html/install.html
.. _Ganeti: http://code.google.com/p/ganeti/
.. _Django: http://djangoproject.com


Getting Started
---------------
.. toctree::
    :maxdepth: 1

    installing
    deploying
    importing
    upgrading


Community & Information
-----------------------
.. toctree::
    :maxdepth: 1

    comm/contact
    comm/issues
    screenshots
    changelog
    license
    faq

Usage
-----
.. toctree::
    :maxdepth: 1

    usage/clusters
    usage/cluster-read-only
    usage/permissions
    usage/sshkeys
    usage/templates
    usage/registration
    usage/caching
    caching
    usage/vnc
    usage/ldap

Developers
----------
.. toctree::
    :maxdepth: 1

    dev/developers
    dev/contributers
    dev/tests
    dev/search
    dev/selenium

References & Guides
~~~~~~~~~~~~~~~~~~~
.. toctree::
    :maxdepth: 1

    ref/rapi-help
    ref/rest-api
    ref/git
    ref/logo
    ref/versions

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

