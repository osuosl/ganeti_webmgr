.. _configuring:

Configuring
===========

After you :ref:`installed <installation>` your |gwm| instance with
:ref:`setup script <setup-script>` it's time for some configuration.

Configuration of |gwm| can be defined with `YAML`_, a human-readable markup
language. |gwm| also supports configuration through ``settings.py``.

.. _`YAML`: http://www.yaml.org/

The YAML configuration file is always named ``config.yml``. You can customize
the location |gwm| looks for this file by setting the ``GWM_CONFIG_DIR``
environmental variable. The current default is ``/opt/ganeti_webmgr/config``.

So by default you will need to put your yaml config in
``/opt/ganeti_webmgr/config/config.yml``. If you want to customize the location
you can set ``GWM_CONFIG_DIR`` like so::

    $ export GWM_CONFIG_DIR='/etc/ganeti_webmgr'

This will cause |gwm| to look for your config file at
``/etc/ganeti_webmgr/config.yml``.

When both ``config.yml`` and ``settings.py`` are present, any settings stored in
``settings.py`` take precedence.

.. Note:: A quick note about settings. Any setting value which contains an
          ``-`` or ``:``, or any other character used by yaml, must be wrapped
          in quotes.

          Example: ``localhost:8000`` becomes ``"localhost:8000"``.

Databases
---------

|gwm| supports PostgreSQL, MySQL, Oracle, and SQLite databases. The type of
database and other configuration options must be defined in either
``settings.py`` or ``config.yml``.

Configuring SQLite in ``config.yml``::

    DATABASES:
        default:
            ENGINE: django.db.backends.sqlite3
            NAME: /opt/ganeti_webmgr/ganeti.db
            USER:      # Not used with sqlite3.
            PASSWORD:  # Not used with sqlite3.
            HOST:      # Set to empty string for localhost.
                             # Not used with sqlite3.
            PORT:      # Set to empty string for default.
                             #Not used with sqlite3.

Configuring SQLite in ``settings.py``::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': install_path('ganeti.db'),
            'USER': '',      # Not used with sqlite3.
            'PASSWORD': '',  # Not used with sqlite3.
            'HOST': '',      # Set to empty string for localhost.
                             # Not used with sqlite3.
            'PORT': '',      # Set to empty string for default.
                             #Not used with sqlite3.
        }
    }

For PostgreSQL, Oracle, and MySQL, replace ``.sqlite`` in the engine field with
``.postgresql_psycopg2``, ``.oracle``, or ``.mysql`` respectively::

    DATABASES:
        default:
            ENGINE: django.db.backends.mysql
            NAME: database_name
            USER: database_user
            PASSWORD: database_password
            HOST: db.example.com
            PORT: # leave blank for default port

Time zone and locale
--------------------

|gwm| supports time zones, translations and localizations for currency, time,
etc. To find the correct time zone for your locale, visit the `List of time
zones`_. For language codes, see `List of language codes`_. Not every language
is supported by |gwm|.

.. _`List of time zones`: http://en.wikipedia.org/wiki/List_of_tz_zones_by_name

.. _`List of language codes`: http://www.i18nguy.com/unicode/language-identifiers.html

Date and datetime format follows the `Django date format`_. For instance,
``d/m/Y`` will result in dates formatted with two-digit days, months, and four-
digit years.

.. _`Django date format`: https://docs.djangoproject.com/en/1.5/ref/templates/builtins/#std:templatefilter-date

A standard configuration might look something like this::

    TIME_ZONE: America/Los_Angeles
    DATE_FORMAT: d/m/Y
    DATETIME_FORMAT: "d/m/Y H:i"

    LANGUAGE_CODE: "en-US"

    # Enable i18n (translations) and l10n (locales, currency, times).
    USE_I18N: True

    # If you set this to False, Django will not format dates, numbers and
    # calendars according to the current locale
    USE_L10N: True

Registration and e-mails
------------------------

To set up |gwm| to send registration emails, you'll need access to an SMTP
server. You can configure the SMTP host, port, and email address::

    EMAIL_HOST: localhost
    EMAIL_PORT: 25
    DEFAULT_FROM_EMAIL: noreply@example.org

For more complicated email setups, refer to the `Django email documentation`_.

.. _`Django email documentation`: http://docs.djangoproject.com/en/dev/topics/email/

Allowing open registration means that users can create their own new accounts in
|gwm|. The users will then have the number of days set in
``ACCOUNT_ACTIVATION_DAYS`` to activate their account::

    ALLOW_OPEN_REGISTRATION: True
    ACCOUNT_ACTIVATION_DAYS: 7

Site root and static files
--------------------------

The site root, static root, and static url must also be set when configuring
|gwm|.

The site root is the subdirectory on the website:
``http://example.com/<SITE_ROOT>``

The static root is the location of static files on the server, and the static
URL is the URL over which the files will be served.

A standard configuration, putting |gwm| at the root of the domain, might look
like this::

    SITE_ROOT:
    STATIC_ROOT: /opt/ganeti_webmgr/collected_static
    STATIC_URL: /static


Other settings
--------------

Set ``VNC_PROXY`` to the hostname of your VNC AuthProxy server.
The VNC AuthProxy does not need to run on the same server as Ganeti Web Manager.

::

    VNC_PROXY: "localhost:8888"

LAZY_CACHE_REFRESH (milliseconds) is the fallback cache timer that is checked
when the object is instantiated. It defaults to 600000ms, or ten minutes.

::

    LAZY_CACHE_REFRESH: 600000

This is how long |gwm| will wait before timing out when requesting data from the
ganeti cluster.

::

    RAPI_CONNECT_TIMEOUT: 3

Sample configuration
--------------------

An annotated sample YAML configuration file is shown below:

.. literalinclude:: ../../../ganeti_webmgr/ganeti_web/settings/config.yml.dist
  :language: yaml