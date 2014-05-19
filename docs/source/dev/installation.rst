:orphan:

.. _developer_installation:

Developer Installation
======================

In order to install |gwm| for end users, one must download ``wheel`` packages.
This, however, is not a case for developers.

You want to work on |gwm|, so you can't install it to virtual environment's
``site-packages``.

**TL;DR;**
::

  $ mkvirtualenv gwm

  (gwm)$ git clone https://github.com/osuosl/ganeti_webmgr.git
  (gwm)$ cd ganeti_webmgr
  (gwm)$ git checkout develop
  (gwm)$ python setup.py develop
  (gwm)$ pip install mysql-python
  (gwm)$ pip install psycopg2
  (gwm)$ cp ./ganeti_webmgr/ganeti_web/settings/settings.py.dist ./ganeti_webmgr/ganeti_web/settings/settings.py
  (gwm)$ vim ./ganeti_webmgr/ganeti_web/settings/settings.py

Requirements
------------

* Python >= 2.6
* your compiler of choice
* ``python-dev`` for compilation of some of |gwm| dependencies
* ``virtualenvwrapper`` (**really recommended**)
* or ``python-environment`` if you can't (or don't want to) install above
  wrapper
* ``libpq-dev`` (Ubuntu/Debian) or ``postgresql-devel`` (CentOS) if you want
  to use PostgreSQL
* ``libmysqlclient-dev`` (Ubuntu/Debian) or ``mysql-devel`` (CentOS) if you
  want to use MySQL


Guide
-----

Virtual environment
~~~~~~~~~~~~~~~~~~~

Start with creating appropriate virtual environment::

  $ mkvirtualenv gwm

This command will work only if you installed ``virtualenvwrapper``.  We
recommend to use it, because it creates virtual environments in
``$HOME/.virtualenvs``, which makes your project directory free of any ``bin``,
``include``, ``lib``, ``local`` or ``share`` directories.

Take a look at :ref:`virtual-environment` page to get better understanding of
how virtual enviroments and ``virtualenvwrapper`` work.

Development package
~~~~~~~~~~~~~~~~~~~

Clone |gwm| repository::

  (gwm)$ git clone https://github.com/osuosl/ganeti_webmgr

You can also `fork on GitHub <https://github.com/osuosl/ganeti_webmgr>`_.

Make sure to switch to ``develop`` branch, as it's the main branch where
development happens::

  (gwm)$ cd ganeti_webmgr
  (gwm)$ git checkout develop

Now it's time to install |gwm| as a development package.  This means even
though |gwm| gets installed as a Python package (and appears on ``pip list``,
and is importable from everywhere in virtual environment), you can still work
on it from the directory you cloned it to.  No need to go into virtualenv's
``lib/python2.x/site-packages/ganeti-webmgr`` directory.

::

  (gwm)$ python setup.py develop

This installs |gwm| dependencies as well, and in some cases requires
compilation.

Databases
~~~~~~~~~

Database drivers / interfaces aren't listed explicitely in |gwm| requirements file, so you have to install them manually.

Make sure you have your dependencies for DBs met.

To install support for **MySQL**::

  (gwm)$ pip install mysql-python

To install support for **PostgreSQL**::

  (gwm)$ pip install psycopg2

To install support for **SQLite**: you don't have to do anything.  It's
included in Python.

Configuration
~~~~~~~~~~~~~

Copy ``settings.py.dist`` to ``settings.py`` within
``ganeti_webmgr/ganeti_webmgr/ganeti_web/settings`` directory.

Edit configuration files in ``ganeti_webmgr/ganeti_webmgr/ganeti_web/settings``
directory:

``base.py``
  Base settings, might not need to be changed.

``settings.py.dist``
  Look there for options you might want to change.  This file exists there
  especially for you.

  .. warning:: Remember to change this file name to ``settings.py``!

Management
~~~~~~~~~~

It's still done via ``manage.py`` script, though the script is now hidden
deeper in directories structure::

  ganeti_webmgr/ganeti_webmgr/manage.py
