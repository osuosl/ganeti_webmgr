.. _setup-script:

Setup script
============

As part of Google Summer of Code 2013 work, |gwm| gained better internal
structure and important feature, which is being a Python package.

This will ensure that future users of |gwm| can install it easily with Python
tools like ``pip``.

What's even more important is that we created an installation script for your
convenience.

setup.sh
--------

Download the ``setup.sh`` script from: https://github.com/pbanaszkiewicz/ganeti_webmgr-setup

Script's workflow
~~~~~~~~~~~~~~~~~

What this script does:

#. Detects user's operating system (Ubuntu, Debian or CentOS).
#. Installs system dependencies (Python, ``python-virtualenv``) via user's OS
   default package manager (``apt`` or ``yum``) [requires ``sudo`` priviledge].
#. Creates :ref:`virtual environment <virtual-environment>` in a local
   directory (or in a directory specified by user).
#. Installs newest ``pip``, ``setuptools`` and ``wheel`` Python packages into
   that virtual environment.
#. Installs |gwm| and it's dependencies into that virtual environment from
   OSUOSL servers (http://ftp.osuosl.org/pub/osl/ganeti-webmgr/).

   These packages are provided as ``.whl`` packages, ie. binary compiled
   packages.  That helps speeding up installation time and requires no
   compilation on end user's side.
#. Creates configuration directory near that virtual environment with sane
   default settings (got from
   https://github.com/pbanaszkiewicz/ganeti_webmgr-config).

.. warning::
  If you happen to have different operating system from these
  :ref:`supported <compatible-operating-systems>` by OSUOSL, you should not
  install ``.whl`` packages from OSUOSL servers.  They're compiled against
  these specific operating systems and their behaviour on other systems /
  architectures might by unpredictable.

Usage
~~~~~

::

  Usage:

      ./setup.sh -h
      ./setup.sh [-d <dir>] [-D <database>] [-N]
      ./setup.sh -u <dir>

  Default installation directory: ./ganeti_webmgr
  Default database server:        SQLite

  Options:
    -h                            Show this screen.
    -d <install_directory>        Specify install directory.
    -D <database_server>          Either 'postgresql' or 'mysql' or 'sqlite'.
                                  This option will try to install required
                                  dependencies for selected database server
                                  (unless -N).  If you don't specify it, SQLite
                                  will be assumed the default DB.
    -N                            Don't try to install system dependencies.
    -u <install_directory>        Upgrade existing installation. Forces -N.

* If no arguments are provided, script tries to install fresh |gwm|.
* If ``-h`` is provided, script displays help page (above).
* If ``-u directory`` is provided, script will try to update |gwm| installed
  within that virtual environment (ie. uses ``directory/bin/pip`` to upgrade).
* To prevent the script from installing system dependencies (for example when
  you're using different operating system or don't trust this script), run it
  with ``-N`` argument.
* To automatically install database dependencies, specify which database server
  you're using via ``-D`` option.

Database requirements
~~~~~~~~~~~~~~~~~~~~~

Depending on your operating system, different packages are needed for different
database servers.

* **MySQL**: ``libmysqlclient18`` on Ubuntu/Debian, or ``mysql-libs`` on CentOS
* **PostgreSQL**: ``libpq5`` on Ubuntu/Debian, or ``postgresql-libs`` on CentOS

These dependencies are required for ``MySQL-python`` and ``psycopg2`` Python
packages to work.
