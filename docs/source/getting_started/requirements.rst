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
* Python >= 2.6
* Python Virtualenv
* git

These dependencies are required to install |gwm| via ``setup.sh`` installation
script.  Follow up to :ref:`installation instructions <installation>`.

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

LDAP
~~~~

LDAP dependencies can be found on the
:ref:`LDAP dependencies <ldap-dependencies>` page.
