.. _build-script:

Dependencies building script
============================

Along with :ref:`setup script <setup-script>` was created script that builds
|gwm| dependencies, both compiled and not, and packages them as ``.whl``
archives.

build_wheels.sh
---------------

You can get it from: https://github.com/pbanaszkiewicz/ganeti_webmgr-setup
(file ``build_wheels.sh``).

Workflow
--------

What this script does:

#. Detects operating system (only Ubuntu, Debian and CentOS are supported) and
   it's architecture.
#. Tries to install necessary dependencies [requires ``sudo`` priviledge]:
    * ``python``
    * ``python-dev``
    * ``python-virtualenv``
    * ``libpq-dev``, ``libmysqlclient-dev`` on Ubuntu and Debian
    * ``postgresql-devel``, ``mysql-devel`` on CentOS
    * ``git``
#. Removes existing :ref:`virtual environment <virtual-environment>`
   installation.
#. Creates new virtual environment in the same destination.
#. Upgrades ``pip``, ``setuptools`` and ``wheel`` (Python packages) in that
   virtual environment.
#. Clones |gwm| if it doesn't exists yet (the script needs it in order to
   build wheel packages of |gwm| dependencies and |gwm| itself).

   .. note::
    You can specify which branch and which git path to clone from.

#. (You can also force cloning).
#. Installs |gwm| into that virtual environment, while creating proper wheel
   packages.
#. Removes virtual environment.

.. warning::
  Remember to keep |gwm| installation directory, wheels output directory and virtual environment apart.


Usage
-----

The only existing dependency you need is ``bash``.  This script takes care of
installing anything additional.  However, if you have some troubles with
dependencies, take a look at :ref:`cant-install-or-run-dependencies`.

Directory structure
~~~~~~~~~~~~~~~~~~~

Directory structure doesn't require any preparation.  For the start, simply download ``build_wheels.sh`` to the empty directory somewhere::

  .
  └── build_wheels.sh

Directories you'll need:

* ``venv`` for virtual environment installation,
* ``gwm`` for |gwm| source code,
* ``wheels`` for wheel packages.

.. hint:: You can totally customize paths to these directories.

These directories will be created after you run ``build_wheels.sh``.


Command line arguments
~~~~~~~~~~~~~~~~~~~~~~

By specifying additional arguments you can change this script's behavior and
some paths it's using.

.. note::
  ``build_wheels.sh`` will work graciously without any additional
  arguments!

.. program:: build_wheels.sh

.. cmdoption:: -e <virtual environment directory>

  :default: ``./venv``

  Path where the script should create a temporary Python virtual
  environment.


.. cmdoption:: -g <Ganeti Web Manager directory>

  :default: ``./gwm``

  Path where |gwm| source code gets cloned to.


.. cmdoption:: -w <wheels output directory>

  :default: ``./wheels``

  Path where output wheel packages are stored.


.. cmdoption:: -a <git remote address>

  :default: ``git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr``

  |gwm| is cloned from this repository address.


.. cmdoption:: -b <branch>

  :default: ``develop``

  Branch that gets checked out when the source is cloned.

.. cmdoption:: -G

  Force cloning |gwm|.

  By default if |gwm| source exists, the script ignores cloning step.  You can
  force it to clone by specifying this argument.


Examples
--------

.. note::
  Remember to make ``build_wheels.sh`` executable::

    $ chmod +x build_wheels.sh


Build for default branch::

  $ ./build_wheels.sh -e ./venv -g ./gwm -w ./wheels

Build for ``master`` branch::

  $ ./build_wheels.sh -e ./venv -g ./ganeti_webmgr -w ./wheels -b master

Build fresh branch ``master`` from GitHub on an unsupported system with all
dependencies install and then upload::

  $ ./build_wheels.sh -G -a https://github.com/osuosl/ganeti_webmgr.git -b master -N
  $ rsync ./wheels rsync@server:/srv/www/wheels


Troubleshooting
---------------

.. _cant-install-or-run-dependencies:

Can't install or run dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're using operating system different from Ubuntu, Debian or CentOS, you
might have troubles installing necessary dependencies.

What this script is looking for:

* ``/usr/bin/sudo``
* ``/bin/rm``
* ``/usr/bin/virtualenv`` (usually ``python-virtualen`` package provides it)
* ``/usr/bin/git`` (usually ``git`` package provides it)

Make sure you have these files present in your system and then run the script
with ``-N`` command line argument.

Can't run ``build_wheels.sh``: permission denied
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script needs to be executable, you can make it by issuing this command::

  $ chmod +x build_wheels.sh
