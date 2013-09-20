.. _configuring:

Configuring
===========

.. todo::
  Go into details on what settings do in settings.py. This should
  probably stick to our specifics, and provide links to Django.
  Probably will want to reference specific sections of docs for
  settings (VNC).

After you :ref:`installed <installation>` your |gwm| instance with
:ref:`setup script <setup-script>` it's time for some configuration.

Mentioned script downloads pre-made configuration for you to the
``/gwm-installation-path/config/``.  Look there and you'll find a file called
``gwm_config.py``.  That's where all the configuration takes place.

.. note::
  |gwm| now installs into virtual environment's Python packages, so you don't
  have to modify files it uses (ie. these in
  ``/venv/lib/python2.x/site-packages/ganet-webmgr/``).


Secrets
-------

First and most important: you should change your sensitive settings.  |gwm|
has two important security-related options: ``SECRET_KEY`` and
``WEB_MGR_API_KEY``.

.. attribute:: gwm_config.SECRET_KEY

  Specifies a value used for hashing and `cryptographic signing <https://docs.djangoproject.com/en/1.4/topics/signing/>`_.  It's very important to keep
  this value secret.
  Changing this value in a deployed application might end up in a flood of
  unexpected security issues, like your users not being able to log in.

.. attribute:: gwm_config.WEB_MGR_API_KEY

  Specifies an API key for authentication scripts that pull information (like
  list of ssh keys) from Ganeti.

There is provided one helper function for your convienience.  With it, you can
load these concealed values from an enviroment variable or from a file.

.. function:: load_secret(env=None, file=None, create_file=True, overwrite_file=False, secret_size=32)

  Tries to get the value from either the enviroment variable or from the
  provided file (in this order).  If it fails and ``create_file`` is set to
  ``True``, the function generates the secret with specified length and stores
  in that file.  Otherwise the function raises ``ImproperlyConfigured``.

  :param string env: enviroment variable name
  :param string file: name of the file with stored secret
  :returns: value from environmental variable or from file
  :rtype: string
  :raises ImproperlyConfigured: if it wasn't possible to get secret from
                                either source and function couldn't create the
                                file

Sample configuration with this helper::

  SECRET_KEY = load_secret(env='GWM_SECRET_KEY', file='.secrets/GWM_SECRET_KEY', create_file=True, secret_size=50)


Database
--------

Even though Django lets you use multiple databases, |gwm| uses only one called
``default``.

.. attribute:: gwm_config.DATABASES

  A dictionary containing database access information.  Its keys are database
  "labels" (and |gwm| only uses the one called ``default``), while the values
  are (again!) dictionaries.

  Configuration is human-friendly and rather easy to change.  Look at the
  examples below.

* **for SQLite**::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'ganeti.db',
            'USER': '',      # not used with SQLite
            'PASSWORD': '',  # not used with SQLite
            'HOST': '',      # not used with SQLite
            'PORT': '',      # not used with SQLite
        },
    }

* **for MySQL**::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'ganeti_webmgr',
            'USER': 'gwm',
            'PASSWORD': 'gwm',
            'HOST': '',      # leave empty for localhost
            'PORT': '',      # leave empty for default port
        },
    }

* **for PostgreSQL**::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'ganeti_webmgr',
            'USER': 'gwm',
            'PASSWORD': 'gwm',
            'HOST': '',      # leave empty for localhost
            'PORT': '',      # leave empty for default port
        },
    }

You can of course leverage helper function to load sensitive data from e.g.
environment variable::

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'ganeti_webmgr',
          'USER': load_secret('GWM_DB_USER', '.secrets/GWM_DB_USER.txt'),
          'PASSWORD': load_secret('GWM_DB_PASS', '.secrets/GWM_DB_PASS.txt', create_file=False),
          'HOST': '',      # leave empty for localhost
          'PORT': '',      # leave empty for default port
      },
  }

Timezones and locale
--------------------

.. attribute:: gwm_config.TIME_ZONE

  The time zone in which |gwm| application works.  `List of time zones <http://en.wikipedia.org/wiki/List_of_tz_zones_by_name>`__.

  For additional information, take a look at Django documentation: https://docs.djangoproject.com/en/1.4/ref/settings/#time-zone.

.. attribute:: gwm_config.DATE_FORMAT

  Pattern used for formatting date (and only date, so no time information
  included).

  Allowed strings: https://docs.djangoproject.com/en/1.5/ref/templates/builtins/#std:templatefilter-date.

.. attribute:: gwm_config.DATETIME_FORMAT

  Pattern used for formatting date and time.

  Allowed strings: https://docs.djangoproject.com/en/1.5/ref/templates/builtins/#std:templatefilter-date.

.. attribute:: gwm_config.LANGUAGE_CODE

  Language of your installation.  Specifies translation used by |gwm|.  For now
  only Greek, Spanish and English are available.

  List of valid language codes: http://www.i18nguy.com/unicode/language-identifiers.html


E-mails
-------

Ensure the server has the ability to send emails or you have access to an SMTP
server.  For more complicatedoutgoing mail setups, please refer to the
`Django email documentation <http://docs.djangoproject.com/en/dev/topics/email/>`_.

.. attribute:: gwm_config.ACCOUNT_ACTIVATION_DAYS

  Number of days users will have to complete their accounts activation after
  they registered.  In case user doesn't activate within that period, the
  account remains permanently inactive.


.. attribute:: gwm_config.ALLOW_OPEN_REGISTRATION

  Whether to allow new users to create new accounts in |gwm|.


.. attribute:: gwm_config.DEFAULT_FROM_EMAIL

  Default: ``webmaster@localhost``.

  Default e-mail address used in communication from Django.


.. attribute:: gwm_config.EMAIL_HOST

  SMTP server host.


.. attribute:: gwm_config.EMAIL_PORT

  SMTP server port.


Cache
-----

Configure the
`Django Cache Framework <http://docs.djangoproject.com/en/dev/topics/cache/>`_
to use a production capable backend in ``end_user.py``.  By default |gwm| is
configured to use the ``LocMemCache`` but it is not recommended for
production.  Use `Memcached <http://memcached.org/>`_ or a similar backend.

::

  CACHES = {
      'default': {
          'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
      }
  }

.. attribute:: gwm_config.LAZY_CACHE_REFRESH

  Default: ``600000`` ms  (10 minutes)

  Fallback cache timer.  Gets checked when object like Virtual Machine, Cluster
  or Node is instantiated.

  More information: :ref:`caching`.


Full-text indexing
------------------

Change the ownership of the ``whoosh_index`` directory to the user running the
web server.  If your using Apache this will be either ``apache``, or
``httpd``.  For nginx, the user will be ``nginx``.  Example::

  $ chown apache:apache whoosh_index/

.. attribute:: gwm_config.HAYSTACK_WHOOSH_PATH

  Path to the directory that stores Whoosh index files.  You should use
  absolute path.

VNC
---

Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
``end_user.py``. The VNC AuthProxy does not need to run on the same server as
|gwm|.

::

  VNC_PROXY = 'my.server.org:8888'


Other settings
--------------

.. attribute:: gwm_config.RAPI_CONNECT_TIMEOUT

  Default: ``3`` (seconds)

  How long to wait for Ganeti clusters to answer GWM queries.


Path helper functions
---------------------

.. versionadded:: 0.11.0

There a few helper functions that have been added to |gwm| settings to help
with getting full paths to files relative to |gwm|.

.. function:: here(path1, [path2, ...])

  Returns an absolute path to the directory settings file is located in.  You
  can append any additional path to it.

  :param string path1: first path
  :returns: absolute project path joined with given paths
  :rtype: string


.. function:: root(path1, [path2, ...])

  Returns an absolute path where the arguments given are joined together with the path to the root of the project.

  :param string path1: first path
  :returns: absolute project path joined with given paths
  :rtype: string


.. function:: app_root(path1, [path2, ...])

  Returns the absoulte path relative to the app directory of GWM. (Where different Django apps are. By default this is the ``ganeti_webmgr`` folder).

  :param string path1: first path
  :returns: absolute project path joined with given paths
  :rtype: string

These are useful if you need to add or change the CSS and/or templates of GWM.
For most cases, you will not need to use these, but they are available if you
do.

Examples::

  here('whoosh_index')  # /path-to-venv/ganeti-webmgr/whoosh_index
  root('some', 'path')  # /path-to-venv/ganeti-webmgr/some/path
  app_root('arbitrary', 'test', 'path')  # /path-to-venv/ganeti-webmgr/ganeti_web/arbitrary/test/path

.. note::
  These helper functions might not be useful to you, in case you installed
  |gwm| as a Python package (happens if you run ``setup.sh`` script).
