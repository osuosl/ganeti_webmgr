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

Installation is now automatic.  You just need to grab one :ref:`Bash script <setup-script>`
and run it with proper arguments.  That script detects your operating system,
installs required dependencies (even for your database of choice!), creates
Python virtual environment and finally installs |gwm| with its own
dependencies.

0. Make sure that all |gwm|'s requirements are met.

1. Download the script to your desired destination (you want to keep that
   script near |gwm| installation path, because you'll use it later to update
   |gwm|):

   ::

    $ cd /opt/ganeti_webmgr/
    $ wget https://raw.github.com/pbanaszkiewicz/ganeti_webmgr-setup/develop/setup.sh

2.  Run ``setup.sh -h`` to get help and see all possible usages of that script.
    To install everything within ``/opt/ganeti_webmgr/gwm`` directory
    (assuming your setup script is in ``/opt/ganeti_webmgr`` and your desired
    database is PostgreSQL)::

    $ ./setup.sh -d ./gwm -D postgresql

Now in ``/opt/ganeti_webmgr/gwm`` is your Python virtual environment.  This
means that all Python packages needed by |gwm| exist within that directory
structure, and not in your global Python packages.  This separation helps
keeping multiple different projects at once and specific dependencies with
pinned versions.

Minimum Configuration
---------------------

When you ran ``setup.sh`` script, it downloaded for you premade configuration
that now resides in ``/opt/ganeti_webmgr/gwm/config``.  Use it as a starting
point.  All configuration options should be well documented and easy to change.

Follow to the :ref:`configuration page <configuring>` for more documentation.

Initializing
------------

Because your |gwm| instance lives within virtual environment, you must get
into it as well::

    $ source gwm/bin/activate

Now all the programs installed to that virtual environment are available for
you (until you issue ``deactivate`` or close your terminal session).

Initialize database
~~~~~~~~~~~~~~~~~~~

* MySQL or SQLite: create new tables and migrate all applications using South::

    $ gwm-manage.py syncdb --migrate

* PostgreSQL: only fresh installation supports PostgreSQL, because there are no
  migrations for this database within |gwm| prior to **version 0.11**::

    $ gwm-manage.py syncdb --all
    $ gwm-manage.py migrate --fake

Search indexes
~~~~~~~~~~~~~~

Build them with::

    $ gwm-manage.py rebuild_index

.. Note::
    Running ``gwm-manage.py update_index`` on a regular basis ensures that the search indexes stay up-to-date when models change in |gwm|.

Next Steps
----------

Congratulations!  |gwm| is now installed and initialized.  Next, you'll want
to look into :ref:`configuring` and :ref:`deploying`, if you are going
to be setting up a production instance.  Otherwise, if you just want to
play around with |gwm|, or are :ref:`developing <development>`, take a look at
:ref:`test-server`.
