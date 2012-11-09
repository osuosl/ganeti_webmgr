Manual installation
===================

Please note that `installation using
Fabric </projects/ganeti-webmgr/wiki/Installation#Install-with-Fabric>`_
is strongly recommended for Ganeti Web Manager version 0.7 and above.

For troubleshooting and help with common errors, see `this
page </projects/ganeti-webmgr/wiki/Errors>`_.

Install dependencies
~~~~~~~~~~~~~~~~~~~~

The following packages are **required** to run Ganeti Web Manager.
Either install these with your system's package manager (recomended), or
directly from the project sites.

-  `Python >= 2.5 but < 3.x <http://www.python.org/>`_ (Python 3.x is
   **not** supported due to backward-compatibility issues)
-  `Python
   Django <http://docs.djangoproject.com/en/dev/intro/install/>`_ with
   specific versions: 1.2 for GWM <0.7, 1.3 for GWM 0.7-0.8, 1.4 for GWM
   >=0.9
-  `Python
   Django-registration <http://bitbucket.org/ubernostrum/django-registration/wiki/Home>`_
-  `Django South
   >=0.7 <http://south.aeracode.org/docs/installation.html>`_
-  `Django Haystack >=1.2.3 <http://haystacksearch.org/>`_
-  `Python Whoosh >= 1.8.3 <http://whoosh.ca/>`_
-  `Django Fields >=
   0.2.0 <https://github.com/svetlyak40wt/django-fields>`_

If you're on Ubuntu >=v10.04, you should be able to install all of these
using `APT <http://en.wikipedia.org/wiki/Advanced_Packaging_Tool>`_ and
`Python pip <http://pypi.python.org/pypi/pip>`_ in one go with the
following command:
::

    sudo apt-get install python2.7 python-django python-django-registration python-django-south
    sudo pip install django-haystack whoosh django-fields

Optional
''''''''

The following packages are **optional**, but may reduce the
functionality of Ganeti Web Manager if not installed.

-  `MySQL <http://dev.mysql.com/doc/refman/5.1/en/installing.html>`_ or
   `PostgreSQL <http://www.postgresql.org/docs/8.1/interactive/installation.html>`_
   (Ganeti Web Manager uses SQLite by default, but using MySQL or
   PostreSQL is suggested for production environments.)
-  `Twisted >=10.2 <http://twistedmatrix.com/trac/>`_ and `Twisted
   Web <http://twistedmatrix.com/trac/wiki/TwistedWeb>`_ (Required for
   `VNC <http://en.wikipedia.org/wiki/Virtual_Network_Computing>`_
   component.)

Get the code
~~~~~~~~~~~~

#. Make sure you have `Git <http://git-scm.com/>`_ installed.
#. Either download and unpack the `latest
   release <https://code.osuosl.org/projects/ganeti-webmgr/files>`_, or
   check it out from the repository:
   ::

       #For public, read-only access use:
       git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr

       #Developers with push access to the repository use:
       git clone git@git.osuosl.org:ganeti/ganeti_webmgr

#. Make a new directory called something like *ganeti\_webmgr\_lib* and
   move into it:
   ::

       mkdir ganeti_webmgr_lib
       cd ganeti_webmgr_lib

#. Check out
   `object\_permissions <http://code.osuosl.org/projects/django-object-log>`_,
   `object\_log <http://code.osuosl.org/projects/django-object-log>`_,
   `muddle\_users <http://code.osuosl.org/projects/muddle-users>`_ and
   `muddle <http://code.osuosl.org/projects/muddle>`_ :

::

    git clone git://git.osuosl.org/gitolite/django/django_object_permissions
    git clone git://git.osuosl.org/gitolite/django/django_object_log
    git clone git://git.osuosl.org/gitolite/django/django_muddle_users
    git clone git://git.osuosl.org/gitolite/django/muddle

#. Change directory into the Ganeti Web Manager root directory and
   symlink the aforementioned modules:
   ::

       cd ../ganeti_webmgr/
       ln -s ../ganeti_webmgr_lib/django_object_permissions/object_permissions/ .
       ln -s ../ganeti_webmgr_lib/django_object_log/object_log/ .
       ln -s ../ganeti_webmgr_lib/django_muddle_users/muddle_users .
       ln -s ../ganeti_webmgr_lib/muddle/muddle .

Optional (for the web-based VNC console)
''''''''''''''''''''''''''''''''''''''''

#. Check out `noVNC <https://github.com/kanaka/noVNC>`_ directly into
   the ganeti\_webmgr root:
   ::

       cd ganeti_webmgr
       git clone git://github.com/kanaka/noVNC.git

#. Check out `Twisted
   VNCAuthProxy. <http://code.osuosl.org/projects/twisted-vncauthproxy>`_
   directly into the ganeti\_webmgr root:
   ::

       cd ganeti_webmgr
       git clone git://git.osuosl.org/gitolite/ganeti/twisted_vncauthproxy

   Instructions for setting up the Twisted VNCAuthProxy are available at
   `http://code.osuosl.org/projects/ganeti-webmgr/wiki/VNC#VNC-AuthProxy <http://code.osuosl.org/projects/ganeti-webmgr/wiki/VNC#VNC-AuthProxy>`_.

Configuration
~~~~~~~~~~~~~

#. In the project root, you'll find a default-settings file called
   **settings.py.dist**. Copy it to **settings.py**:
   ::

       cp settings.py.dist settings.py

#. If you want to use another database engine besides the default SQLite
   (not recommended for production), edit **settings.py**, and edit the
   following lines to reflect your wishes:
   ::

       1DATABASE_ENGINE = ''   # <-- Change this to 'mysql', 'postgresql', 'postgresql_psycopg2' or 'sqlite3'
       2DATABASE_NAME = ''     # <-- Change this to a database name, or a file for SQLite
       3DATABASE_USER = ''     # <-- Change this (not needed for SQLite)
       4DATABASE_PASSWORD = '' # <-- Change this (not needed for SQLite)
       5DATABASE_HOST = ''     # <-- Change this (not needed if database is localhost)
       6DATABASE_PORT = ''     # <-- Change this (not needed if database is localhost)

#. Initialize Database:
   ::

       ./manage.py syncdb --migrate

#. Build the search indexes
   ::

       ./manage.py rebuild_index

#. Everything should be all set up! Run the development server with:
   ::

       ./manage.py runserver

Additional configuration for production servers:
''''''''''''''''''''''''''''''''''''''''''''''''

Deploying a production server requires additional setup steps.

#. Change your **SECRET\_KEY** and **WEB\_MGR\_API\_KEY** to unique (and
   hopefully unguessable) strings in your settings.py.
#. Configure the `Django Cache
   Framework <http://docs.djangoproject.com/en/dev/topics/cache/>`_ to
   use a production capable backend in **settings.py**. By default
   Ganeti Web Manager is configured to use the **LocMemCache** but it is
   not recommended for production. Use Memcached or a similar backend.
   ::

       1CACHES = {
       2    'default': {
       3        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
       4    }
       5}

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
   apache. <http://docs.djangoproject.com/en/dev/howto/deployment/modwsgi/>`_
   Here is an example mod\_wsgi file:
   ::

        1import os
        2import sys
        3
        4path = '/var/lib/django/ganeti_webmgr'
        5if path not in sys.path:
        6    sys.path.append(path)
        7
        8os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
        9
       10import django.core.handlers.wsgi
       11application = django.core.handlers.wsgi.WSGIHandler()

#. Enable the `periodic cache
   updater </projects/ganeti-webmgr/wiki/Cache_System#Periodic-Cache-Refresh>`_.
   **NOTE**: Do not run the cache updater as ``root``.
   ::

       twistd --pidfile=/tmp/gwm_cache.pid gwm_cache

   You may encounter an issue where twisted fails to start and gives you
   an error.
   This is usually caused by the environment variable PYTHONPATH not
   being
   exported correctly if you switch to superuser 'su -'. To fix it type:
   ::

       export PYTHONPATH="." 

   Than ``exit`` out of root.
#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   **settings.py**. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.
   ::

       1VNC_PROXY = 'my.server.org:8888'
