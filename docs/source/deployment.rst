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
#. Deploy fabric environment: fab dev deploy or fab prod deploy
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
-  :doc:`manual-install`

.. _Fabric: http://docs.fabfile.org/

Compatibility
-------------

Ganeti Web Manager is compatible with the following:

-  `Ganeti <http://code.google.com/p/ganeti/>`_: **>= v2.2.x** is
   supported. **v2.1.x** and **v2.0.x** are unsupported and sometimes
   work but can cause problems (see `#8973 <http://code.osuosl.org/issues/8973>`_). Lower
   versions are **not** supported.
-  **Browsers:** `Mozilla Firefox <http://mozilla.com/firefox>`_ >=
   v3.x, `Google Chrome <http://www.google.com/chrome/>`_ or
   `Chromium <http://code.google.com/chromium/>`_. Other contemporary
   browsers may also work, but are not supported. (The web-based VNC
   console requires browser support of
   `WebSockets <http://en.wikipedia.org/wiki/WebSockets>`_ and
   `HTML5 <http://en.wikipedia.org/wiki/Html5.>`_)
-  **Databases:** MySQL or SQLite. SQLite is not recommended in
   production environments.
-  **Operating Systems:** GWM has been tested on Debian 7, Ubuntu 11.10,
   12.04 and CentOs 5 and 6. Debian 6 is supported, provided the Pip,
   Virtualenv and Fabric packages are updated to the versions listed
   below.

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
       fab prod deploy

       # development environment
       fab dev deploy

#. Activate virtual environment

   ::

       source bin/activate

Configuration
-------------

#. In the project root, you'll find a default-settings file called
   **settings.py.dist**. Copy it to **settings.py**:

   ::

       cp settings.py.dist settings.py

#. If you want to use another database engine besides the default SQLite
   (not recommended for production), edit **settings.py**, and edit the
   following lines to reflect your wishes.

   .. Note:: Postgresql is not supported at this time and the
             install will fail (See issue `#3237 <http://code.osuosl.org/issues/3237>`_).

   ::

       DATABASE_ENGINE = ''   # <-- Change this to 'mysql', 'postgresql', 'postgresql_psycopg2' or 'sqlite3'
       DATABASE_NAME = ''     # <-- Change this to a database name, or a file for SQLite
       DATABASE_USER = ''     # <-- Change this (not needed for SQLite)
       DATABASE_PASSWORD = '' # <-- Change this (not needed for SQLite)
       DATABASE_HOST = ''     # <-- Change this (not needed if database is localhost)
       DATABASE_PORT = ''     # <-- Change this (not needed if database is localhost)

#. Initialize Database:

   ::

       ./manage.py syncdb --migrate

#. Build the search indexes

   ::

       ./manage.py rebuild_index

   .. Note:: Running **./manage.py update\_index** on a regular basis
             ensures that the search indexes stay up-to-date when models change in
             Ganeti Web Manager.

#. Everything should be all set up! Run the development server with:

   ::

       ./manage.py runserver

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
   documentation <http://docs.djangoproject.com/en/1.2/topics/email/>`_.
#. Follow the django guide to `deploy with
   apache. <https://docs.djangoproject.com/en/1.4/howto/deployment/wsgi/modwsgi/>`_
   Here is an example mod\_wsgi file:

   ::

       import os
       import sys

       path = '/var/lib/django/ganeti_webmgr'

       # activate virtualenv
       activate_this = '%s/bin/activate_this.py' % path
       execfile(activate_this, dict(__file__=activate_this))

       # add project to path
       if path not in sys.path:
           sys.path.append(path)

       # configure django environment
       os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

       import django.core.handlers.wsgi
       application = django.core.handlers.wsgi.WSGIHandler()

#. Enable the `periodic cache
   updater </projects/ganeti-webmgr/wiki/Cache_System#Periodic-Cache-Refresh>`_.

   .. Note:: Do not run the cache updater as ``root``.

   ::

       twistd --pidfile=/tmp/gwm_cache.pid gwm_cache

   You may encounter an issue where twisted fails to start and gives you
   an error.
   This is usually caused by the environment variable PYTHONPATH not
   being
   exported correctly if you switch to superuser 'su -'. To fix it type:

   ::

       export PYTHONPATH="."

   Then ``exit`` out of root.

#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   **settings.py**. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.

   ::

       VNC_PROXY = 'my.server.org:8888'
