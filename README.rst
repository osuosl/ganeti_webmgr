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
* `Documentation <http://ganeti-webmgr.readthedocs.org/en/latest/>`_
* `Mailing List <http://groups.google.com/group/ganeti-webmgr>`_
* `Twitter <http://twitter.com/ganetiwebmgr>`_
* IRC: ``#ganeti-webmgr`` on freenode.net


Installation
============

.. NOTE::
    Installing via the ``setup.sh`` script is now the preferred method.  That
    script does everything for you.  However it's still possible to install GWM
    in not-that-much automatic way.

Installation script
-------------------

Get ``setup.sh`` from https://github.com/pbanaszkiewicz/ganeti_webmgr-setup.
Make it executable, run ``./setup.sh -h`` to get help message and then install
GWM.  Notice, that this script can upgrade your installation in future.

For development
---------------

Get yourself the ``virtualenvwrapper``.  For your sanity.  Then proceed with
installation:

.. code-block:: console

    $ mkvirtualenv gwm
    (gwm)$ git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr
    (gwm)$ cd ganeti_webmgr
    (gwm)$ python setup.py develop

And that's it, you can now safely work on GWM.

Manual installation
-------------------

#) Install dependencies: Python, Pip, Virtualenv

#) Get the Ganeti Web Manager code: Clone from the repository or download
   a release tarball

#) Create a virtual environment in your desired location and install GWM in
   there by issueing ``python setup.py install`` in GWM directory (after you
   unzipped the tarball or cloned the repository)

#) Configure settings: in directory ``ganeti_webmgr/ganeti_web/settings`` copy
   ``end_user.py.dist`` to ``end_user.py`` and make any modifications

#) Sync database, then run the server: ``./ganeti_webmgr/manage.py syncdb --migrate``, then
   ``./ganeti_webmgr/manage.py runserver``

Related Topics
--------------

* `Troubleshoot <https://code.osuosl.org/projects/ganeti-webmgr/wiki/Fabric-troubleshooting>`_ an installation using Fabric

* `More on manual installation <https://code.osuosl.org/projects/ganeti-webmgr/wiki/Manual-installation>`_

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

* `Virtualenv`_ >= 1.6.1

.. _Python: http://python.org/
.. _Virtualenv: http://pypi.python.org/pypi/virtualenv

Other requirements are either `Virtualenv`_ dependencies or will get installed
by setup script.

* install Virtualenv:

.. code-block:: console

    $ sudo apt-get install python-virtualenv


Configuration
=============

In the ``ganeti_webmgr/ganeti_web/settings`` directory, you'll find a default
settings file called ``end_user.py.dist``.  Copy it to ``end_user.py``:

.. code-block:: console

    $ cp end_user.py.dist end_user.py

If you want to use another database engine besides the default SQLite (not
recommended for production), then in settings edit the following lines to
reflect your wishes:

.. code-block:: python

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

.. WARNING::
    PostgreSQL support was fixed just recenly, check if your GWM version has
    it.  See issue `#3237`_.

.. _#3237: https://code.osuosl.org/issues/3237

Initialize Database:

.. code-block:: console

    $ ./ganeti_webmgr/manage.py syncdb --migrate

Build the search indexes:

.. code-block:: console

    $ ./ganeti_webmgr/manage.py rebuild_index

.. NOTE::
    Running ``./ganeti_webmgr/manage.py update_index`` on a regular basis
    ensures that the search indexes stay up-to-date when models change in
    Ganeti Web Manager.

Everything should be all set up! Run the development server with:

.. code-block:: console

    $ ./ganeti_webmgr/manage.py runserver

Additional configuration for production servers
-----------------------------------------------

Deploying a production server requires additional setup steps.

1. Change the ownership of the ``whoosh_index`` directory to apache

.. code-block:: console

    $ chown apache:apache whoosh_index/

2. Change your ``SECRET_KEY`` and ``WEB_MGR_API_KEY`` to unique (and hopefully
   unguessable) strings in your ``end_user.py`` settings file.

3. Configure the `Django Cache Framework`_ to use a production capable backend
   in ``end_user.py``.  By default Ganeti Web Manager is configured to use the
   ``LocMemCache`` but it is not recommended for production.  Use Memcached or
   a similar backend.

.. code-block:: python

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
   in ``end_user.py``. For more complicated outgoing mail setups, please refer to the `Django Email documentation`_.

6. Follow the `Django guide <http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/>`_ to deploy with apache.
   Here is an example mod_wsgi file:

.. code-block:: python

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
   ``end_user.py``.  The VNC AuthProxy does not need to run on the same server as Ganeti Web Manager.

.. code-block:: python

    VNC_PROXY = 'my.server.org:8888'

Also see the `Install documentation <https://gwm.readthedocs.org/en/latest/deployment.html>`_.

.. _Django Cache Framework: http://docs.djangoproject.com/en/dev/topics/cache/
.. _Django Email documentation: http://docs.djangoproject.com/en/1.2/topics/email/


Ganeti RAPI users and passwords
===============================

Before you can start using Ganeti Web Manager, you will need to create a user
and password on the Ganeti cluster.

Here is an example with user "jack" and password "abc123":

.. code-block:: console

    $ echo -n 'jack:Ganeti Remote API:abc123' | openssl md5

Add the hash to the RAPI users file and restart ganeti-rapi. Depending on the
version of Ganeti you are running, you will need to either use
``/var/lib/ganeti/rapi_users`` (Ganeti <=2.3.x ) or
``/var/lib/ganeti/rapi/users`` (Ganeti >=2.4.x ).

An example hash entry might look like the following:

.. code-block:: console

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

.. code-block:: console

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

Enabling in settings file
-------------------------

Set the host and port that the proxy will be running at with the ``VNC_PROXY``
setting.  For development this is typically ``"localhost:8888"`` but for
production you would use the name of the server its running on.  See the
instructions in ``end_user.py`` for more details.

Starting the Daemon
-------------------

Twisted VNC Authproxy is started with twistd, the twisted daemon.  Eventually
we will include ``init.d`` scripts for better managing the daemon.  You may
want to open port 8888 in your firewall for production systems.

.. code-block:: console

    $ twistd --pidfile=/tmp/proxy.pid -n vncap

Starting Flash Policy Server
----------------------------

Browsers that do not support WebSockets natively are supported through the use
of a flash applet.  Flash applets that make use of sockets must retrieve
a policy file from the server they are connecting to.  Twisted VNCAuthProxy
includes a policy server.  It must be run separately since it requires a root
port.  You may want to open port 843 in your firewall for production systems.

Start the policy server with twistd:

.. code-block:: console

    $ sudo twistd --pidfile=/tmp/policy.pid -n flashpolicy


Possible issues
---------------

You may encounter an issue where twisted fails to start and gives you an error.
This is usually caused by the environment variable ``PYTHONPATH`` not being
exported correctly if you sudo up to root.  To fix it type:

.. code-block:: console

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
