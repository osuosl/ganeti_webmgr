.. _requirements:

Requirements
------------

Operating system
~~~~~~~~~~~~~~~~

We officially support Ubuntu 11.10, Ubuntu 12.04 and CentOS 6.  |gwm| is also
known to work on Debian 7 and CentOS 5.

More on :ref:`compatibility page <compatible-operating-systems>`.

Base
~~~~

* sudo
* git

These dependencies are required to install |gwm| via ``setup.sh`` installation
script.  Follow up to :ref:`installation instructions <installation>`.

During installation, if ``python`` and ``python-virtualenv`` are not installed,
they will be installed.

.. _other_platforms:

Other Platforms
```````````````

For operating systems other than CentOS and Debian, it will be necessary to
install several required packages that the script handles, specifically:

* Python
* ``python-virtualenv``

Virtualenv is used to manage |gwm|'s dependencies without touching other
software on the system.

When running the ``setup.sh`` script, pass the ``-N`` flag to disable
installation of these packages.

Databases
~~~~~~~~~

All database dependencies are installed **automatically** during ``setup.sh``
run.  All you need is ``sudo`` priviledge.  If you have any issues, please
refer to Django database
`documentation <https://docs.djangoproject.com/en/1.4/topics/install/#get-your-database-running>`__.

If you, for any reason, want to install these database dependencies on your
own, here's the list:

**MySQL**
  requires ``MySQL-python`` package installed within virtual environment,
  which in turn requires ``libmysqlclient18`` on Ubuntu/Debian and
  ``mysql-libs`` on CentOS.

**PostgreSQL**
  requires ``psycopg2`` package installed within virtual environment, which in
  turn requires ``libpq5`` on Ubuntu/Debian and ``postgresql-libs`` on CentOS.

If you're using the ``setup.sh`` script these database dependencies should be
installed for you. But if it runs into errors, these are the dependencies needed.

LDAP
~~~~

LDAP dependencies can be found on the
:ref:`LDAP dependencies <ldap-dependencies>` page.

VNCAuthProxy
~~~~~~~~~~~~

VNCAuthProxy, is used to connect the VNC web frontend to a Ganeti VM's VNC Console.
This project is built on twisted and for encryption requires openssl and FFI
development headers.

On CentOS, the OpenSSL package is ``openssl-devel`` and on Ubuntu/Debian its
``libssl-dev``. The LibFFI package is ``libffi-devel`` on CentOS and ``libffi-dev``
on Ubuntu/Debian.

These packages are necessary to install VNCAuthProxy and should be installed
before the setup script is run.
