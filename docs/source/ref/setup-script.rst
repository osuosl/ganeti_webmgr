.. _setup-script:

Setup script
============

As part of Google Summer of Code 2013 work, |gwm| gained better internal
structure and important feature, which is being a Python package.

This will ensure that future users of |gwm| can install it easily with Python
tools like ``pip``.

What's even more important is that we created an installation script for your
convenience.

.. note::
  Take a look at :ref:`installation instructions <installation>` to see how
  you should install |gwm|.

setup.sh
--------

The ``setup.sh`` script can be located in the ``scripts/`` folder at the root of
the |gwm| project folder.

Workflow
--------

What this script does:

#. Detects operating system (only Ubuntu, Debian and CentOS are supported) and
   it's architecture.
#. Installs system dependencies (Python, ``python-virtualenv``) via user's OS
   default package manager (``apt`` or ``yum``) [requires ``sudo`` priviledge].
#. Creates :ref:`virtual environment <virtual-environment>` in local directory
   (or in directory specified by user).
#. Installs newest ``pip``, ``setuptools`` and ``wheel`` Python packages into
   that virtual environment.
#. Installs |gwm| and it's dependencies from OSUOSL servers
   (http://ftp.osuosl.org/pub/osl/ganeti-webmgr/) into that virtual
   environment.
   These packages are provided as ``.whl`` packages, ie. binary compiled
   packages.  That helps speeding up installation time and requires no
   compilation on end user's side.

.. warning::
  If you happen to have different operating system from these
  :ref:`supported <compatible-operating-systems>` by OSUOSL, you should not
  install ``.whl`` packages from OSUOSL servers.  They're compiled against
  these specific operating systems and their behavior on other systems /
  architectures might by unpredictable.

.. warning::
  This script does not auto-configure your installation.  You have to manually
  do this.


Database requirements
---------------------

Depending on your operating system, different packages are needed for different
database servers.

* **MySQL**: ``libmysqlclient18`` on Ubuntu/Debian, or ``mysql-libs`` on CentOS
* **PostgreSQL**: ``libpq5`` on Ubuntu/Debian, or ``postgresql-libs`` on CentOS

These dependencies are required for ``MySQL-python`` and ``psycopg2`` Python
packages to work.

The script will get appropriate packages for you, unless you use ``-N`` flag.
For more information, take a look at :ref:`setup-script-cli-arguments`.


Usage
-----

.. _setup-script-cli-arguments:

Command line arguments
~~~~~~~~~~~~~~~~~~~~~~

.. program:: setup.sh

.. cmdoption:: -d <install directory>

  :default: ``/opt/ganeti_webmgr``

  Directory for the virtual environment.


.. cmdoption:: -w <wheels (local/remote) directory location>

  :default: ``http://ftp.osuosl.org/pub/osl/ganeti-webmgr``

  Wheel packages are read from that path.  The path can be either local
  (eg. ``./gwm/wheels``) or remote (eg.
  ``http://ftp.osuosl.org/pub/osuosl/wheels``).

  This also assumes the directory structure for the wheels package is structured
  according to how the :ref:`build-script`
  :ref:`structures files <build-folder-structure>`.

  .. warning:: Don't change it unless you know what you're doing!


.. cmdoption:: -D <database server>

  :default: SQLite

  If you provide ``postgresql`` or ``mysql``, the script will try to install
  system and Python dependencies for selected database, unless ``-N`` flag is
  set.


.. cmdoption:: -N

  Skip installing system dependencies.  You want to use this flag if you either
  don't trust this script or if you have unsupported operating system.

  .. warning::
    When ``-N`` flag isn't provided, the script will run **sudo** to get user's
    permission to install some system dependencies.


.. cmdoption:: -u <install directory>

  :default: ``./ganeti_webmgr``

  Upgrade existing installation.  Point the script to directory being a virtual
  environment, ie. containing ``bin/pip`` (which is required in order to
  upgrade).


.. cmdoption:: -h

  Display help.


Examples
~~~~~~~~

Run with default settings::

  $ ./scripts/setup.sh

Install PostgreSQL::

  $ ./scripts/setup.sh -d ./gwm -D postgresql

Skip installing system dependencies::

  $ ./scripts/setup.sh -N

Upgrade existing installation::

  $ ./scripts/setup.sh -u ./existing_gwm

Generate wheels on your own with :ref:`building script<build-script>`::

  $ ./scripts/build_wheels.sh -e ./venv_whl -w ./wheels
  $ ./scripts/setup.sh -d ./ganeti_webmgr -w ./wheels

or send wheels to remote location and install from it::

  $ ./scripts/build_wheels.sh -e ./venv_whl -w ./wheels
  $ rsync ./wheels rsync@foo.example.org:/srv/www/wheels
  $ ./scripts/setup.sh -d ./ganeti_webmgr -w http://foo.example.org/wheels


Directory structure
~~~~~~~~~~~~~~~~~~~

After installing |gwm| via ``setup.sh`` this is what you get::

  ./ganeti_webmgr
  ├── bin
  ├── config
  ├── include
  │   └── ...
  ├── lib
  │   └── ...
  └── local
      └── ...

Directories ``bin``, ``include``, ``lib`` or ``local`` are
:ref:`virtual-environment` specific - don't bother about them. The directory
``config`` on the other hand is important to you: this is where your |gwm|
configuration resides.

Troubleshooting
---------------

Can't run ``setup.sh``: permission denied
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script needs to be executable, you can make it by issuing this command::

  $ chmod +x ./scripts/setup.sh
