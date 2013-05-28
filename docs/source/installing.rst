.. _installation:

Installation
============

Currently we have use `Fabric`, a tool for streamlining administration
tasks, to deploy |gwm|.

Before installing |gwm|, make sure you have all the required
:ref:`dependencies` installed.


Installing
----------

#. Download, or wget, and unpack the `latest
   release <http://code.osuosl.org/projects/ganeti-webmgr/files>`_,
   currently this is `0.9.2
   <https://code.osuosl.org/attachments/download/3231/ganeti-webmgr-0.9.2.tar.gz>`_.

   ::

      # wget or download from your browser of choice
      wget https://code.osuosl.org/attachements/download/3231/ganeti-webmgr-0.9.2.tar.gz

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

#. Deploy Ganeti Web Manager with `mod_wsgi and Apache`:
   :ref:`deploying`.


.. _install-additional-config:

Additional configuration for production servers
-----------------------------------------------

Deploying a production server requires additional setup steps.

#. Change the ownership of the ``whoosh_index`` directory to apache

   ::

       chown apache:apache whoosh_index/

#. Change your **SECRET\_KEY** and **WEB\_MGR\_API\_KEY** to unique (and
   hopefully unguessable) strings in your settings.py.

#. Configure the `Django Cache
   Framework <http://docs.djangoproject.com/en/dev/topics/cache/>`_ to
   use a production capable backend in **settings.py**. By default
   Ganeti Web Manager is configured to use the **LocMemCache** but it is
   not recommended for production. Use Memcached or a similar backend.

   ::

       CACHES = {
           'default': {
               'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
           }
       }

#. For versions >= 0.5 you may need to add the full filesystem path to
   your templates directory to **``TEMPLATE_DIRS``** and remove the
   relative reference to **``'templates'``**. We've had issues using
   wsgi not working correctly unless this change has been made.

#. Ensure the server has the ability to send emails or you have access
   to an SMTP server. Set **``EMAIL_HOST``**, **``EMAIL_PORT``**, and
   **``DEFAULT_FROM_EMAIL``** in settings.py. For more complicated
   outgoing mail setups, please refer to the `django email
   documentation <http://docs.djangoproject.com/en/dev/topics/email/>`_.

#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   **settings.py**. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.

   ::

       VNC_PROXY = 'my.server.org:8888'
