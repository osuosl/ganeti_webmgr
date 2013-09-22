.. _build-script:

Dependencies building script
============================

Along with :ref:`setup script <setup-script>` was created script that builds
|gwm| dependencies, both compiled and not, and packages them as ``.whl``
archives: ``build_wheels.sh``.

build_wheels.sh
---------------

You can get it from: https://github.com/pbanaszkiewicz/ganeti_webmgr-setup

Workflow
~~~~~~~~

What this script does:

#. Detects operating system (only Ubuntu, Debian and CentOS are supported) and
   it's architecture.
#. Tries to install required dependencies [requires ``sudo`` priviledge]:
    * ``python``
    * ``python-dev``
    * ``python-virtualenv``
    * ``libpq-dev``, ``libmysqlclient-dev`` on Ubuntu and Debian
    * ``postgresql-devel``, ``mysql-devel`` on CentOS
    * ``git``
#. Removes existing virtual environment installation.
#. Creates new virtual environment in the same destination.
#. Upgrades ``pip``, ``setuptools`` and ``wheel`` in that virtual environment.
#. Clones |gwm| if it doesn't exists yet.

   .. warning::
    For now the script uses ``master`` branch to build dependencies.

#. (You can also force cloning despite circumstances).
#. Installs |gwm| into that virtual environment, creating proper wheel packages
   simultaneously.
#. Removes virtual environment.

.. warning::
  Remember to keep |gwm| installation directory and wheels output directory
  apart from installation virtual environment.

Usage
~~~~~

::

  Usage:
      ./build_wheels.sh -h
      ./build_wheels.sh [-e <dir>] [-g <dir>] [-G] [-w <dir>]

  Default virtual environment path:   ./venv
  Default GWM clone path:             ./gwm
  Default wheels output directory:    ./wheels

  Wheels are put in subfolders in this pattern:
      ./wheels/{distribution}/{version}/{architecture}/

  Options:
    -h                        Show this screen.
    -e <environment dir>      Specify virtual environment path. This gets erased
                              on every runtime.
    -g <GWM dir>              Where to clone GWM. If this path exists, GWM is not
                              cloned and existing copy is used instead.
    -G                        Remove GWM dir and therefore force cloning GWM.
    -w <wheels dir>           Where to put built wheel packages.

Example usage
~~~~~~~~~~~~~

Build for default (``master``) branch::

  $ ./build_wheels.sh -e ./venv -g ./gwm -w ./wheels

Build for ``develop`` branch::

  $ git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr
  $ cd ganeti_webmgr
  $ git checkout develop
  $ cd ..
  $ ./build_wheels.sh -e ./venv -g ./ganeti_webmgr -w ./wheels

Build and upload::

  $ ./build_wheels.sh -e ./venv -g ./gwm -w ./wheels
  $ rsync ./wheels rsync@server:/srv/www/wheels
