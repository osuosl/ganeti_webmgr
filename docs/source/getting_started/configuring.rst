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
``gwm_config.py``.  It's where all the configuration takes place.

.. note::
  |gwm| now installs into virtual environment's Python packages, so you don't
  have to modify files it uses.


Secrets
-------

First and most important: you should change your secrets.  |gwm| has two
important configuration options: ``SECRET_KEY`` and ``WEB_MGR_API_KEY``.

.. attribute:: gwm_config.SECRET_KEY

  Specifies a value used for hashing and `cryptographic signing <https://docs.djangoproject.com/en/1.4/topics/signing/>`_.  It's very important to keep
  this value secret.
  Changing this value in a deployed application might end up in a flood of
  unexpected security issues, like your users not able to log in.

.. attribute:: gwm_config.WEB_MGR_API_KEY

  Specifies an API key for authentication scripts that pull information (like
  list of ssh keys) from Ganeti.

There are provided several helper functions for your convienience.  With them,
you can load these concealed values from enviroment variable or from file.

.. function:: get_env_or_file_secret(env_var, file_location)

  Tries to get the value from the enviroment variable and falls back to
  grabbing the contents of the provided file.

  If both are empty, or an :py:exc:`IOError` exception is raised, this returns
  ``None``.

  :param string env_var: enviroment variable name
  :param string file_location: where fallback file is located
  :returns: value from environmental variable or from file
  :rtype: None or string

.. function:: get_env_or_file_or_create(env_var, file_location[, secret_size=16])

  A wrapper around :func:`get_env_or_file_secret` that will create the file
  if it does not already exist.  The resulting file's contents will be
  a randomly generated value.

  :param string env_var: enviroment variable name
  :param string file_location: where fallback file is located
  :param int secret_size: length of randomly selected sequence
  :returns: value from environmental variable or from file
  :rtype: None or string
  :raises Exception: when neither environmental variable nor file contain
                     anything

Sample configuration with one of these helpers::

  SECRET_KEY = get_env_or_file_or_create('GWM_SECRET_KEY', '.secrets/GWM_SECRET_KEY', 50)


Database
--------

Even though Django lets you use multiple databases, |gwm| uses only one called
``default``.

.. attribute:: gwm_config.DATABASES

  A dictionary containing database access information.  Its keys are database
  "labels" (and |gwm| only uses the one called ``default``), while the values
  are (again!) dictionaries.

  Configuration is human-friendly and rather easy.  Look at the examples below.

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

You can of course leverage helper functions to load sensitive data from e.g.
environment variable::

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'ganeti_webmgr',
          'USER': get_env_or_file_secret('GWM_DB_USER', '.secrets/GWM_DB_USER.txt'),
          'PASSWORD': get_env_or_file_secret('GWM_DB_PASS', '.secrets/GWM_DB_PASS.txt'),
          'HOST': '',      # leave empty for localhost
          'PORT': '',      # leave empty for default port
      },
  }

Timezones and locale
--------------------

.. attribute:: gwm_config.TIME_ZONE

  nothing yet

.. attribute:: gwm_config.DATE_FORMAT

  nothing yet

.. attribute:: gwm_config.DATETIME_FORMAT

  nothing yet

.. attribute:: gwm_config.LANGUAGE_CODE

  nothing yet


Full-text indexing
------------------

Change the ownership of the ``whoosh_index`` directory to the user running the
web server.  If your using Apache this will be either ``apache``, or
``httpd``.  For nginx, the user will be ``nginx``.  Example::

  $ chown apache:apache whoosh_index/


E-mails
-------

Ensure the server has the ability to send emails or you have access
to an SMTP server. Set **EMAIL_HOST**, **EMAIL_PORT**, and
**DEFAULT_FROM_EMAIL** in ``end_user.py``. For more complicated
outgoing mail setups, please refer to the `django email
documentation <http://docs.djangoproject.com/en/dev/topics/email/>`_.


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


VNC
---

Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
``end_user.py``. The VNC AuthProxy does not need to run on the same server as
|gwm|.

::

  VNC_PROXY = 'my.server.org:8888'


Other helper functions
----------------------

.. versionadded:: 0.11.0

There a few helper functions that have been added to |gwm| settings to help
with getting full paths to files relative to |gwm|.

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

  root('some', 'path')  # Will return /path/to/ganeti_webmgr/some/path
  app_root('arbitrary', 'test', 'path')  # Will return /path/to/ganeti_webmgr/ganeti_web/arbitrary/test/path

.. note::
  These helper functions might not be useful to you, in case you installed
  |gwm| as a Python package (happens if you run ``setup.sh`` script).
