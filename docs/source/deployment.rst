Installation
============

.. Note: Installing from the tarball is the preferred method. After
         installing the dependencies, please download the tarball instead of
         cloning the repository.

Overview
~~~~~~~~

#. Install dependencies: Python, Pip, Fabric, VirtualEnv
#. Get the Ganeti Web Manager code: Clone from the repository or
   download a release tarball
#. Deploy fabric environment: fab dev deploy or fab deploy
#. Configure Settings: Copy settings.py.dist to settings.py and make
   any modifications
#. Sync database, then run the server: ./manage.py syncdb --migrate,
   then ./manage.py runserver

This section explains how to automatically install Ganeti Web Manager
using Fabric_. Fabric simplifies the installation process by
automatically installing dependencies into a virtual environment.

Related Topics:

-  Read more about why :doc:`fabric-recommend`
-  :doc:`fabric-install`

.. _Fabric: http://docs.fabfile.org/

Compatibility
-------------

Ganeti Web Manager is compatible with the following:

- `Ganeti`_: Ganeti **2.4.x--2.6.0** are supported. Earlier versions are
  unsupported; they may occasionally work, but should not be relied upon.
- **Browsers:** `Mozilla Firefox`_ 3.x and newer, and recent `Google
  Chrome`_/`Google Chromium`_, are supported. Other contemporary browsers may
  also work, but are not supported. The web-based VNC
  console requires browser support of WebSockets and HTML5.
- Databases: While all databases supported by Django should work, the GWM team
  officially supports `SQLite`_ and `MySQL`_.
- Operating Systems: GWM is officially supported on Ubuntu 11.10, Ubuntu
  12.04, and CentOS 6. It is also known to work on Debian 7 and CentOS 5.
  Debian 6 should work, provided the Pip, Virtualenv and Fabric packages are
  updated to the versions listed below.

.. _Ganeti: http://code.google.com/p/ganeti/
.. _Mozilla Firefox: http://mozilla.com/firefox
.. _Google Chrome: http://www.google.com/chrome/
.. _Google Chromium: http://www.chromium.org/
.. _SQLite: https://sqlite.org/
.. _MySQL: https://www.mysql.com/

Dependencies
------------

-  Python: >=2.5, python >=2.6 recommended
-  `Pip <http://www.pip-installer.org/en/latest/index.html>`_ >= 0.8.2
-  Fabric_ >=1.0.1
-  `VirtualEnv <http://pypi.python.org/pypi/virtualenv>`_ >= 1.6.1

Pip is required for installing Fabric and a useful tool to install
Virtualenv

::

    #pip
    sudo apt-get install python-pip

    # devel libraries may be needed for some pip installs
    sudo apt-get install python-dev

Install Fabric and Virtualenv

::

    # install fabric and virtualenv
    sudo apt-get install python-virtualenv
    sudo apt-get install fabric

.. Note:: The use of pip to install system packages is not recommended,
          please use your system's package manager to install Virtualenv and
          Fabric.

Install with Fabric
-------------------

#. Either download and unpack the `latest
   release <http://code.osuosl.org/projects/ganeti-webmgr/files>`_, or
   check it out from the repository:

   ::

       git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr

#. Switch to project directory

   ::

       # Fabric commands only work from a directory containing a fabfile
       cd ganeti_webmgr/

#. Run Fabric to automatically create python virtual environment with
   required dependencies. Choose either production or development
   environment

   ::

       # production environment
       fab deploy

       # development environment
       fab dev deploy

#. Activate virtual environment

   ::

       source venv/bin/activate

Configuration
-------------

#. In the project root, you'll find a default-settings file called
   **settings.py.dist**. Copy it to **settings.py**:

   ::

       cp settings.py.dist settings.py

#. If you want to use another database engine besides the default SQLite
   (not recommended for production), edit **settings.py**, and edit the
   following lines to reflect your wishes.

   .. Note:: Postgresql is supported as of version .10
   ::

       DATABASE_ENGINE = ''   # <-- Change this to 'mysql', 'postgresql', 'postgresql_psycopg2' or 'sqlite3'
       DATABASE_NAME = ''     # <-- Change this to a database name, or a file for SQLite
       DATABASE_USER = ''     # <-- Change this (not needed for SQLite)
       DATABASE_PASSWORD = '' # <-- Change this (not needed for SQLite)
       DATABASE_HOST = ''     # <-- Change this (not needed if database is localhost)
       DATABASE_PORT = ''     # <-- Change this (not needed if database is localhost)

#. Initialize Database:

   MySQL/SQLite:
   ::

       ./manage.py syncdb --migrate

   Postgres:

   .. Note:: This assumes your doing a fresh install of GWM on a new Postgres database.
   ::

       ./manage.py syncdb --all
       ./manage.py migrate --fake

#. Build the search indexes

   ::

       ./manage.py rebuild_index

   .. Note:: Running **./manage.py update\_index** on a regular basis
             ensures that the search indexes stay up-to-date when models change in
             Ganeti Web Manager.

#. Everything should be all set up! Run the development server with:

   ::

       ./manage.py runserver

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
#. Follow the django guide to `deploy with
   apache. <https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/>`_
   Here is an example mod\_wsgi file:

   ::

       import os
       import sys

       path = '/var/lib/django/ganeti_webmgr'

       # activate virtualenv
       activate_this = '%s/venv/bin/activate_this.py' % path
       execfile(activate_this, dict(__file__=activate_this))

       # add project to path
       if path not in sys.path:
           sys.path.append(path)

       # configure django environment
       os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

       import django.core.handlers.wsgi
       application = django.core.handlers.wsgi.WSGIHandler()

#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   **settings.py**. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.

   ::

       VNC_PROXY = 'my.server.org:8888'
