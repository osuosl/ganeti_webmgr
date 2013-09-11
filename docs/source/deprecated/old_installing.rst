.. _old_installation:

Deprecated: Installation
========================

.. warning::
  This document is deprecated as of |gwm| version 0.11.

We use `Fabric`, a tool for streamlining administration tasks, to deploy |gwm|.

Before installing |gwm|, make sure you have all the required
:ref:`deprecated_dependencies` installed.


Installing
----------

#. Download and unpack the `latest
   release <http://code.osuosl.org/projects/ganeti-webmgr/files>`_,
   currently this is |release|.

#. Change to the project directory.

   ::

       cd ganeti_webmgr

#. Run Fabric to automatically create a python virtual environment and
   install required dependencies. This may take a few minutes.

   ::

       # Deploy a production environment
       fab deploy

   .. versionchanged:: 0.10
      `fab prod deploy` is now `fab deploy`. `fab dev deploy` is still
      the same.

   .. Note:: If you would like a more noisy output, adding `v`, as in
             `fab v deploy`, will provide more verbosity.

#. While in the project root, copy the default settings file
   **settings.py.dist** to **settings.py**:

   ::

       cp settings.py.dist settings.py


Minimum Configuration
---------------------

Getting |gwm| up and running requires a minimum configuration of a
database server. If you don't have a database server available, and are
fine using SQLite, you can skip this step.

#. Edit **settings.py** and change the database backend to your
   preferred database along with filling any any relevant details
   relating to your database setup.


   ::

       'default': {
           # Add 'postgresql_psycopg2', 'postgresql', 'mysql',
           # 'sqlite3' or 'oracle'.
           'ENGINE': 'django.db.backends.',

           # Or path to database file if using sqlite3.
           'NAME': 'ganeti.db',

           # Not used with sqlite3.
           'USER':     '',

           # Not used with sqlite3.
           'PASSWORD': '',

           # Set to empty string for localhost. Not used with sqlite3.
           'HOST':     '',

           # Set to empty string for default. Not used with sqlite3.
           'PORT':     '',
       }


Initializing
------------

#. Activate the Python Virtualenv:

   ::

       source venv/bin/activate

#. Initialize Database:

   MySQL/SQLite:

   ::

       # Create new tables and migrate all apps using southdb
       ./manage.py syncdb --migrate

   Postgres:

   .. Note:: This assumes your doing a fresh install of |gwm| on a new Postgres database.

   ::

       ./manage.py syncdb --all
       ./manage.py migrate --fake

#. Build the search indexes

   ::

       ./manage.py rebuild_index

   .. Note:: Running **./manage.py update\_index** on a regular basis
             ensures that the search indexes stay up-to-date when models change in
             Ganeti Web Manager.

Next Steps
----------

Congradulations! |gwm| is now installed and initialized. Next, you'll want
to look into :ref:`configuring` and :ref:`deployment <deployment>`, if you are
going to be setting up a production instance. Otherwise, if you just want to
play around with |gwm|, or are :ref:`developing <development>`, take a look at
:ref:`development-server`.
