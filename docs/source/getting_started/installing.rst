.. _installation:

Installation
============

.. warning::
    Prior to version 0.11, the preferred way of installing |gwm| was by using
    ``fabric``.  It is **no longer** a default way of installing |gwm|.  If
    you have older |gwm|, look at :ref:`these instructions <old_installation>`.

This instruction covers installation steps for end users.  It is not intended
for |gwm| developers or people installing unstable version.  If you want to
play with unstable |gwm|, please follow
:ref:`instructions for developers <developer_installation>`.

Installing
----------

Installation is now automatic. There is now a shell script detects your
operating system, installs required dependencies (even for your database of
choice!), creates Python virtual environment and finally installs |gwm| with its
own dependencies.

#. Make sure that all |gwm|'s :ref:`requirements` are met.

#. Next you need the latest release of |gwm| which is |release|. You can
   download that here: |release_tarball|. You can also clone the repo and
   checkout the latest tag as well::

   $ git clone https://github.com/osuosl/ganeti_webmgr.git
   $ git checkout $VERSION

  .. note:: Replace $VERSION with the version you want to deploy, such as
            |release|

  It doesn't actually matter where you put these, it will only be used for
  installation, which will eventually install the project to another location,
  which by default is ``/opt/ganeti_webmgr``.

#.  Once you've got the project, you will use our shell script to install things.
    First, cd to the |gwm| project folder::

    $ cd ./ganeti_webmgr

    Next run ``./scripts/setup.sh -h`` to get help and see all possible usages
    of our shell script. There are different options for installing to different
    locations, as well as installing different database dependencies.

#. Now that you've looked at the options, you'll want to actuall install |gwm|.
   By default, it will install to ``/opt/ganeti_webmgr`` and will not install any
   database dependencies. To do this install run the following::

   $ ./scripts/setup.sh

   If you want to install |gwm| with mysql support, which means installing your
   systems mysql-client libraries, development headers, and the python mysql
   package run::

   $ ./scripts/setup.sh -D mysql

  .. Note:: You will likely need to run this as root as it requires permissions
          to install packages and create directories in ``/opt``.

.. _vncauthproxy-script:

VNC AuthProxy startup script
----------------------------

|gwm| provides an in-browser VNC console. For more information, see
:ref:`VNC <vnc-authproxy>`. In order to use the VNC console, you must run VNC
AuthProxy, which comes with |gwm|.

VNC AuthProxy can be set up to start on boot if wanted. To do so, it is
necessary to set up an init script to manage the daemon. These vary by
platform, so depending on what kind of system you are running |gwm| on, there are
a few choices.

CentOS and Ubuntu
~~~~~~~~~~~~~~~~~

.. important::
   These scripts were written for CentOS 6.5 and Ubuntu 12.04.


If you are running CentOS, copy the file ``scripts/vncauthproxy/init-centos``
to ``/etc/init.d/vncauthproxy`` and install the service::

    $ sudo cp /path/to/gwm/source/scripts/vncauthproxy/init-centos /etc/init.d/vncauthproxy
    $ sudo chkconfig --add vncauthproxy

Otherwise, if you are running Ubuntu, copy the file
``scripts/vncauthproxy/init-ubuntu`` to ``/etc/init.d/vncauthproxy`` and
install the service::

    $ sudo cp /path/to/gwm/scripts/vncauthproxy/init-ubuntu /etc/init.d/vncauthproxy
    $ sudo update-rc.d vncauthproxy defaults

The ``vncauthproxy`` service is installed and can be started::

    $ sudo service vncauthproxy start

systemd
~~~~~~~

For systems running ``systemd``, a basic systemd script is provided. It
has been tested on Debian 8.

Copy the file ``scripts/vncauthproxy/init-systemd`` to
``/lib/systemd/system/vncauthproxy.service`` and enable the service::

    $ sudo cp /path/to/gwm/scripts/vncauthproxy/init-systemd /lib/systemd/system/vncauthproxy.service
    $ sudo systemctl enable vncauthproxy

The script supports variables for PIDFILE, LOGFILE, PORT, and INTERFACE, which
can be set in '/etc/defaults/vncauthproxy'.

To set the location of the ``twistd`` daemon to somewhere other than
``/opt/ganeti_webmgr/bin/twistd``, it is at this time necessary to modify the
service file directly.

Minimum Configuration
---------------------

There are defaults for most settings, however, **there are no defaults set for
database settings.** Make sure to set these or you will run into problems with
the rest of the installation.

See :ref:`configuration page <configuring>` for documentation on configuring
|gwm|.

.. _initializing:

Initializing
------------

Because your |gwm| instance lives within virtual environment, you must activate
the virtual environment in order to access GWM::

    $ source /opt/ganeti_webmgr/bin/activate

Now all the programs installed to that virtual environment are available for
you (until you issue ``deactivate`` or close your terminal session).

We'll be using the ``django-admin.py`` tool to run commands to administer our
app from this point forward. You might be familiar with ``manage.py``, which is
essentially what ``django-admin.py`` is. However, we need to tell
``django-admin.py`` what settings to use, in order for it to work. To do this
run the following command::

    $ export DJANGO_SETTINGS_MODULE="ganeti_webmgr.ganeti_web.settings"

You only need to run this once each time you activate the virtual environment,
or if you prefer, each time you run ``django-admin.py`` you can provided the
``--settings`` argument::

    $ django-admin.py $CMD --settings "ganeti_webmgr.ganeti_web.settings"

.. Note:: Replace $CMD with the command you actually need to run. Also note that
          the ``--settings`` flag must come after the $CMD being run.

Initialize database
~~~~~~~~~~~~~~~~~~~

* MySQL or SQLite: create new tables and migrate all applications using South::

    $ django-admin.py syncdb --migrate

* PostgreSQL: only fresh installation supports PostgreSQL, because there are no
  migrations for this database within |gwm| prior to **version 0.11**::

    $ django-admin.py syncdb --all
    $ django-admin.py migrate --fake

Update Cache
~~~~~~~~~~~~

Prior to **version 0.11** when migrations were run, we would automatically
update the cache of RAPI data in the Database, however running this during
migrations was prone to a lot of errors, so it is now its own command. Run the
following to update the cache::

  $ django-admin.py refreshcache

.. versionadded:: 0.11

Search indexes
~~~~~~~~~~~~~~

Build them with::

    $ django-admin.py rebuild_index

.. Note::
    Running ``django-admin.py update_index`` on a regular basis ensures that the search indexes stay up-to-date when models change in |gwm|.

Next Steps
----------

Congratulations!  |gwm| is now installed and initialized.  Next, you'll want
to look into :ref:`configuring` and :ref:`deployment`, if you are going
to be setting up a production instance.

Otherwise, if you just want to play around with |gwm|, or are :ref:`developing
<development>`, take a look at the :ref:`development-server`.
