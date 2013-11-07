.. Ganeti Web Manager documentation master file, created by
   sphinx-quickstart on Fri Oct 26 11:40:24 2012.

Ganeti Web Manager
==================

|gwm| is a Django_ based web frontend for managing Ganeti_ virtualization clusters. Since Ganeti only provides a command-line interface, |gwm|'s goal is to provide a user friendly web interface to Ganeti via Ganeti's :ref:`Remote API <rapi>`. On top of Ganeti it provides a permission system for managing access to clusters and virtual machines, an in browser VNC console, and vm state and resource visualizations. You can see a few screenshots :ref:`here <screenshots>`.

If you don't already have a Ganeti cluster setup, these directions_ can help you get started. 

If you are looking for support, please :ref:`contact us <contact>`. 

If you are looking to deploy |gwm| for the first time, check out our :ref:`installation` guide. 

If you already have a |gwm| instance running it might be time to :ref:`upgrade <upgrading>`.

Finally, if you would like to report a bug or request a feature, please :ref:`file an issue <issues>`.

|gwm| is licensed under the :ref:`GPLv2 <license>`. It is currently developed and maintained by the Oregon State University Open Source Lab and a handful of volunteers. If you would like to get involved in development see our :ref:`development <development>` guide.


.. _directions: http://docs.ganeti.org/ganeti/current/html/install.html
.. _Ganeti: http://code.google.com/p/ganeti/
.. _Django: http://djangoproject.com


Getting Started
---------------
.. toctree::
    :maxdepth: 1

    getting_started/requirements
    getting_started/installing
    getting_started/configuring
    getting_started/deploying
    getting_started/importing

User Guide
----------
.. toctree::
    :maxdepth: 1

    usage/configuring
    usage/upgrading
    usage/clusters
    usage/virtualmachines
    usage/nodes
    usage/templates
    features/permissions
    features/objectlog
    features/vnc
    features/sshkeys
    features/ldap
    features/templates
    features/clusters
    features/cluster-read-only
    features/registration
    features/caching
    features/ganetiviz

Contributing
------------
.. toctree::
    :maxdepth: 1

    dev/issues

.. toctree::
    :maxdepth: 2

    dev/developers

.. toctree::
    :maxdepth: 1

    dev/process 

Project Information
-------------------
.. toctree::
    :maxdepth: 1

    project_info/compatibility
    project_info/changelog
    project_info/history
    project_info/design
    project_info/contact
    project_info/screenshots
    project_info/license
    project_info/faq
    project_info/contributors


References
~~~~~~~~~~
.. toctree::
    :maxdepth: 1

    ref/rapi-help
    ref/rest-api
    ref/git
    ref/logo
    ref/versions
    ref/setup-script
    ref/build-script
    ref/venv

Deprecated
==========
.. toctree::
    :maxdepth: 1

    deprecated/old_dependencies
    deprecated/old_installing
    deprecated/old_upgrading
    deprecated/old_caching


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
