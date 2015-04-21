.. _build-script:

Dependencies building script
============================

Along with the :ref:`setup script <setup-script>`, ``build_wheels.sh`` was
created as a  script that builds |gwm| dependencies, both compiled and not, and
packages them as ``.whl`` archives.

You can find the build script in |gwm|'s script directory at
``./scripts/build_script.sh``


.. _build-folder-structure:

Folder Structure
----------------

Wheels are put in subfolders in this pattern::

    $wheels_dir/{distribution}/{version}/{architecture}/

The :ref:`setup-script`'s -w flag expects the wheels to be in this folder
structure. So using ``build_wheels.sh`` to create these is required, unless you
create the directory structure yourself.


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
#. Installs |gwm| into that virtual environment, while creating proper wheel
   packages.
#. Removes virtual environment.

.. warning::
  Remember to keep wheels output directory and virtual environment apart.


Usage
-----

The only existing dependency you need is ``bash``.  This script takes care of
installing anything additional.  However, if you have some troubles with
dependencies, take a look at :ref:`cant-install-or-run-dependencies`.

To use the script, you simply run it. If you want to build wheels packages for
a different version of |gwm|, you simply need to ``git checkout`` the branch or
tag that you want to build the wheels packages for.

Directory structure
~~~~~~~~~~~~~~~~~~~

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

.. cmdoption:: -w <wheels output directory>

  :default: ``./wheels``

  Path where output wheel packages are stored.

.. cmdoption:: -N

  Skip installing system dependencies.

Examples
--------

Default options::
  $ ./scripts/build_wheels.sh

Here's another way to do the above, specifiying the locations::

  $ ./scripts/build_wheels.sh -e ./venv -w ./wheels

Build wheels without dependencies (an unsupported OS), and upload the wheels::

  $ ./scripts/build_wheels.sh -N
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
