==================
Ganeti Web Manager
==================

Ganeti Web Manager is a Django-based web application that allows administrators
and clients access to their ganeti clusters.

Ganeti compatibility:

* >=2.4.x - supported
* 2.2.2 - mostly supported
* 2.3.1 - mostly supported
* 2.1.x - mostly supported
* 2.0.x - unsupported but may work
* 1.x   - unsupported

Browser compatibility:

* Mozilla Firefox >= 3.x
* Chrome / Chromium

The VNC console requires WebSockets or flash support and HTML5 support in the
browser.

Links
=====

* `Project page <http://code.osuosl.org/projects/ganeti-webmgr>`_
* `Documentation <https://gwm.readthedocs.org/en/latest/>`_
* `Mailing List <http://groups.google.com/group/ganeti-webmgr>`_
* `Twitter <http://twitter.com/ganetiwebmgr>`_
* IRC: ``#ganeti-webmgr`` on freenode.net


Installation
============

.. NOTE::
    Installing from the tarball is the preferred method. After installing
    the dependencies, please download the tarball instead of cloning the
    repository.

Overview
--------

#) Install dependencies: Python, Pip, Fabric, VirtualEnv

#) Get the Ganeti Web Manager code: Clone from the repository or download
   a release tarball

#) Deploy fabric environment: fab dev deploy or fab deploy

#) Configure Settings: Copy ``settings.py.dist`` to ``settings.py`` and make
   any modifications

#) Sync database, then run the server: ``./manage.py syncdb --migrate``, then
   ``./manage.py runserver``

This section explains how to automatically install Ganeti Web Manager using
`Fabric`_.  Fabric simplifies the installation process by automatically
installing dependencies into a virtual environment.

.. _Fabric: http://docs.fabfile.org/en/1.0.1/index.html

Related Topics
--------------

* Read more about `why Fabric is strongly recommended <https://code.osuosl.org/projects/ganeti-webmgr/wiki/Fabric_is_strongly_recommended>`_

* `Troubleshoot <https://code.osuosl.org/projects/ganeti-webmgr/wiki/Fabric-troubleshooting>`_ an installation using Fabric

* `Manual installation <https://code.osuosl.org/projects/ganeti-webmgr/wiki/Manual-installation>`_

Compatibility
-------------

Ganeti Web Manager is compatible with the following:

`Ganeti`_
  Ganeti >= v2.2.x is supported. v2.1.x and v2.0.x are unsupported and
  sometimes work but can cause problems (see `#8973`_). Lower versions are
  **not** supported.

Browsers
  `Mozilla Firefox`_ >= v3.x, `Google Chrome`_ or `Chromium`_.

  Other contemporary browsers may also work, but are not supported. (The
  web-based VNC console requires browser support of `WebSockets`_ and `HTML5`_.

Databases
  MySQL or SQLite. SQLite is not recommended in production environments.

Operating systems
  GWM has been tested on Debian 7, Ubuntu 11.10, 12.04 and CentOs 5 and 6.
  Debian 6 is supported, provided the Pip, Virtualenv and Fabric packages are
  updated to the versions listed below.

.. _#8973: https://code.osuosl.org/issues/8973
.. _Ganeti: http://code.google.com/p/ganeti/
.. _Mozilla Firefox: http://mozilla.com/firefox
.. _Google Chrome: http://www.google.com/chrome/
.. _Chromium: http://code.google.com/chromium/
.. _WebSockets: http://en.wikipedia.org/wiki/WebSockets
.. _HTML5: http://en.wikipedia.org/wiki/Html5

Dependencies
------------

* `Python`_ >=2.5, Python >=2.6 recommended

* `Pip`_ >= 0.8.2

* `Fabric`_ >=1.0.1

* `Virtualenv`_ >= 1.6.1

.. _Python: http://python.org/
.. _Pip: http://www.pip-installer.org/en/latest/index.html
.. _Fabric: http://docs.fabfile.org/en/1.0.1/index.html
.. _Virtualenv: http://pypi.python.org/pypi/virtualenv

`Pip`_ is required for installing `Fabric`_ and useful tool to install
`Virtualenv`_.

* install pip:

.. sourcecode:: bash

    $ sudo apt-get install python-pip

* development libraries may be needed for some pip installs:

.. sourcecode:: bash

    $ sudo apt-get install python-dev

* install Fabric and Virtualenv:

.. sourcecode:: bash

    $ sudo apt-get install python-virtualenv fabric

.. NOTE::
    the use of pip to install system packages is not recommended, please use
    your system's package manager to install Virtualenv and Fabric.

Install with `Fabric`_
----------------------

Either download and unpack the "latest release" from
`here <http://code.osuosl.org/projects/ganeti-webmgr/files>`_, or check it out
from the repository:

.. sourcecode:: bash

    $ git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr

Switch to project directory (Fabric commands only work from a directory
containing a ``fabfile.py``):

.. sourcecode:: bash

    $ cd ganeti_webmgr/

Run `Fabric`_ to automatically create python virtual environment with required
dependencies.  Choose either production or development environment

* production environment:

.. sourcecode:: bash

    $ fab deploy

* development environment:

.. sourcecode:: bash

    $ fab dev deploy

* activate virtual environment:

.. sourcecode:: bash

    $ source venv/bin/activate


Configuration
=============

In the project root, you'll find a default settings file called
``settings.py.dist``.  Copy it to ``settings.py``:

.. sourcecode:: bash

    $ cp settings.py.dist settings.py

If you want to use another database engine besides the default SQLite (not
recommended for production), edit ``settings.py``, and edit the following
lines to reflect your wishes ():

.. sourcecode:: python

    DATABASE_ENGINE = ''   # <-- Change this to 'mysql', 'postgresql',
                           #     'postgresql_psycopg2' or 'sqlite3'
    DATABASE_NAME = ''     # <-- Change this to a database name, or a file for
                           #     SQLite
    DATABASE_USER = ''     # <-- Change this (not needed for SQLite)
    DATABASE_PASSWORD = '' # <-- Change this (not needed for SQLite)
    DATABASE_HOST = ''     # <-- Change this (not needed if database is
                           #     localhost)
    DATABASE_PORT = ''     # <-- Change this (not needed if database is
                           #     localhost)

.. NOTE::
    PostgreSQL is not supported at this time and the installation will fail,
    see issue `#3237`_.

.. _#3237: https://code.osuosl.org/issues/3237

Initialize Database:

.. sourcecode:: bash

    $ ./manage.py syncdb --migrate

Build the search indexes:

.. sourcecode:: bash

    $ ./manage.py rebuild_index

.. NOTE::
    Running ./manage.py update_index on a regular basis ensures that the
    search indexes stay up-to-date when models change in Ganeti Web Manager.

Everything should be all set up! Run the development server with:

.. sourcecode:: bash

    $ ./manage.py runserver

Additional configuration for production servers
-----------------------------------------------

Deploying a production server requires additional setup steps.

1. Change the ownership of the ``whoosh_index`` directory to apache

        $ chown apache:apache whoosh_index/

2. Change your ``SECRET_KEY`` and ``WEB_MGR_API_KEY`` to unique (and hopefully
    unguessable) strings in your ``settings.py``.

3. Configure the `Django Cache Framework`_ to use a production capable backend
   in ``settings.py``.  By default Ganeti Web Manager is configured to use the
   ``LocMemCache`` but it is not recommended for production.  Use Memcached or
   a similar backend.

.. sourcecode:: python

    CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
       }
    }

4. For versions >= 0.5 you may need to add the full filesystem path to your
   templates directory to ``TEMPLATE_DIRS`` and remove the relative reference
   to 'templates'. We've had issues using wsgi not working correctly unless
   this change has been made.

5. Ensure the server has the ability to send emails or you have access to an
   SMTP server. Set ``EMAIL_HOST``, ``EMAIL_PORT``, and ``DEFAULT_FROM_EMAIL``
   in ``settings.py``. For more complicated outgoing mail setups, please refer to the `Django Email documentation`_.

6. Follow the`Django guide <http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/>`_ to deploy with apache.
   Here is an example mod_wsgi file:

.. sourcecode:: python

    import os
    import sys

    path = '/var/lib/django/ganeti_webmgr'

    # activate virtualenv
    activate_this = '%s/venv/bin/activate_this.py' % path
    execfile(activate_this, dict(__file__=activate_this))

    # add project to path
    if path not in sys.path:
        sys.path.append(path)

    # configure django environment
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

    import django.core.handlers.wsgi
    application = django.core.handlers.wsgi.WSGIHandler()

7. Set ``VNC_PROXY`` to the hostname of your VNC AuthProxy server in
   ``settings.py``.  The VNC AuthProxy does not need to run on the same server as Ganeti Web Manager.

.. sourcecode:: python

    VNC_PROXY = 'my.server.org:8888'

Also see the `Install documentation <https://gwm.readthedocs.org/en/latest/deployment.html>`_.

.. _Django Cache Framework: http://docs.djangoproject.com/en/dev/topics/cache/
.. _Django Email documentation: http://docs.djangoproject.com/en/1.2/topics/email/


Ganeti RAPI users and passwords
===============================

Before you can start using Ganeti Web Manager, you will need to create a user
and password on the Ganeti cluster.

Here is an example with user "jack" and password "abc123":

.. sourcecode:: bash

    $ echo -n 'jack:Ganeti Remote API:abc123' | openssl md5

Add the hash to the RAPI users file and restart ganeti-rapi. Depending on the
version of Ganeti you are running, you will need to either use
``/var/lib/ganeti/rapi_users`` (Ganeti <=2.3.x ) or
``/var/lib/ganeti/rapi/users`` (Ganeti >=2.4.x ).

An example hash entry might look like the following:

.. sourcecode:: bash

    # Hashed password for jack
    jack {HA1}54c12257ee9be413f2f3182435514aae write

Also see `managing clusters documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Managing_Clusters#Ganeti-RAPI-users-and-passwords>`_.


Importing a Cluster
===================

#) Use the admin user created during syncdb to log in.

#) Import a cluster:  Clusters -> Add Cluster

#) Fill out properties and click save

When the cluster is created it will automatically synchronize the list of
Virtual Machines with information from the Ganeti cluster.

Also see `importing cluster documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Importing_a_Cluster>`_.


Users, Groups and Permissions
=============================

Permissions may be granted to both clusters and virtual machines. The
permissions system is intended to allow users to manage themselves. Any object
that can have its permissions edited will have a Users tab.


Adding users to objects:

#) Navigate to Group, Cluster, or Virtual Machine detail page

#) Click Add New User

#) Select user or group

#) Select permissions

#) Save


Updating permissions:

#) Navigate to Group, Cluster, or Virtual Machine detail page

#) Click Users tab

#) Click permissions column

#) Select permissions and save


Deleting permissions:

#) Navigate to Group, Cluster, or Virtual Machine detail page

#) Click Users tab

#) Click the delete icon

Deleting a user will remove all permissions, and other properties associated
with the user such as cluster quotas.

Users may belong to any number of user groups.  User groups can be assigned
permissions and quotas just like users.  Users inherit permissions from groups
and may act on their behalf to create virtual machines.

Also see `permissions documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Permissions>`_.


Assigning Quotas
================

Quotas restrict the usage of cluster resources by users and groups. Default
quotas can be set by editing clusters, if no quota is set unlimited access is
allowed. This will affect all users and groups.


The default quota can be overridden on the cluster users page:

#) Clusters -> Cluster -> Users

#) Click on the quota

#) Edit values


Leaving a value empty specifies unlimited access for that resource.

Also see `quotas documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Permissions#Quotas>`_.


Orphaned Virtual Machines
=========================

You can find Virtual Machines with no permissions via Admin -> Orphaned VMs.
This will force a synchronization of all clusters and display Virtual Machines
that do not have any permissions assigned.

You only need to grant permissions directly on virtual machines if you are
granting access to non-admin users.

Also see `the documentation page about orphaned virtual machines <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Managing_Clusters#Orphaned-Virtual-Machines>`_.


Cache System
============

Ganeti Web Manager uses a cache system that stores information about Ganeti
clusters in the database. This allows the following:

.. sourcecode:: bash

      ---  Ganeti  ---
     /                \
    /                  \
 Cluster ->       <-   Bulk
  Model  <- cache <-  Updater

* Permissions are stored in the database and are associated to the cached
  objects

* The cached data can be searched and or filtered

* Limits the amount of traffic between the web server and Ganeti cluster.

The cache system is transparent and will load cached data automatically when
the object is initialized.

Also see `cache system documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/Cache_System>`_.


VNC
===

Ganeti Web Manager provides an in browser console using `noVNC`_, an HTML5
client.  noVNC requires WebSockets to function.  Support for older browsers is
provided through a flash applet that is used transparently in the absence of
WebSockets.

.. _noVNC: https://github.com/kanaka/noVNC

Also see `the VNC documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/VNC>`_.


VNC AuthProxy
=============

`VNC Auth proxy`_ is required for the console tab to function. VNC servers do
not speak websockets and our proxy allows your ganeti cluster to sit behind a
firewall, VPN, or NAT.

Enabling in ``settings.py``
---------------------------

Set the host and port that the proxy will be running at with the ``VNC_PROXY``
setting.  For development this is typically ``"localhost:8888"`` but for
production you would use the name of the server its running on.  See the
instructions in ``settings.py`` for more details.

Starting the Daemon
-------------------

Twisted VNC Authproxy is started with twistd, the twisted daemon.  Eventually
we will include ``init.d`` scripts for better managing the daemon.  You may
want to open port 8888 in your firewall for production systems.

.. sourcecode:: bash

    $ twistd --pidfile=/tmp/proxy.pid -n vncap

Starting Flash Policy Server
----------------------------

Browsers that do not support WebSockets natively are supported through the use
of a flash applet.  Flash applets that make use of sockets must retrieve
a policy file from the server they are connecting to.  Twisted VNCAuthProxy
includes a policy server.  It must be run separately since it requires a root
port.  You may want to open port 843 in your firewall for production systems.

Start the policy server with twistd:

.. sourcecode:: bash

    $ sudo twistd --pidfile=/tmp/policy.pid -n flashpolicy


Possible issues
---------------

You may encounter an issue where twisted fails to start and gives you an error.
This is usually caused by the environment variable ``PYTHONPATH`` not being
exported correctly if you sudo up to root.  To fix it type:

.. sourcecode:: bash

    $ export PYTHONPATH="."

Try executing Twisted again and it should work.

.. _VNC Auth Proxy: http://code.osuosl.org/projects/twisted-vncauthproxy

Also see `the VNC AuthProxy documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/VNC#VNC-Authproxy>`_.


SSH Keys
========

Ganeti Web Manager allows users to store SSH Keys.  Each virtual machine has a
view that will return SSH keys for users with access.  This can be used as a
Ganeti post-install hook to deploy user's keys on the VMs.

To allow VMs to copy keys, copy ``util/hooks/sshkeys.sh`` to the instance
definition hooks directory on every node in the cluster and make the file
executable.  Next, add the required variables to the variant config file
or main instance definition config file.  The config file can be found in
``util/hooks/sshkeys.conf`` and includes documentation for each variable.

Also see `the SSH Keys documentation page <http://code.osuosl.org/projects/ganeti-webmgr/wiki/PermissionsSSHKeys>`_.
