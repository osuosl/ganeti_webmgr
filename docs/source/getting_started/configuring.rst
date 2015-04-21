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
``settings.py`` or ``config.yml``. **These settings are not set by default**
like most other settings in |gwm|. Be sure to actually configure your database
settings.

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
            'NAME': '/opt/ganeti_webmgr/ganeti.db',
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

    # config.yml
    DATABASES:
        default:
            ENGINE: django.db.backends.mysql
            NAME: database_name
            USER: database_user
            PASSWORD: database_password
            HOST: db.example.com
            PORT: # leave blank for default port

Secret Keys
-----------

By default |gwm| creates a ``SECRET_KEY`` and a ``WEB_MGR_API_KEY`` for you the
first time you run a command using ``django-admin.py``, and puts this key into a
file located at ``/opt/ganeti_webmgr/.secrets/SECRET_KEY.txt``. This is to make
initial setup easier, and less hassle for you. This key is used for protection
against CSRF attacks as well as encrypting your Ganeti cluster password in the
database. Once set, you should avoid changing this if possible.

If you want to have better control of this setting you can set the
``SECRET_KEY`` setting in ``config.yml`` like so::

    SECRET_KEY: ANW61553mYBKJft6pYPLf1JbTeHKLutU

Please do not use this value, but instead generate something random yourself.
You do **not** want to share this, or make it publicly accessible. This can
be used to avoid protections |gwm| has implemented for you.

If you are using the :ref:`sshkeys` feature to add keys to VMs with |gwm|, you
will also need to set the ``WEB_MGR_API_KEY`` setting in ``config.yml`` or keep
the value created for you in
``/opt/ganeti_webmgr/.secrets/WEB_MGR_API_KEY.txt``. This is the same value you
will use when running the ``sshkeys.py`` or ``sshkeys.sh`` scripts. Similarly,
it should be something impossible to guess, much like the ``SECRET_KEY``
setting::

    WEB_MGR_API_KEY: 3SqmsCnNiuDY9lAVIh3Tx3RIJfql6sIc

Again, do not use the value above. If anyone gains access to this key, **and**
you are using the sshkeys feature, it will allow them to add arbitrary ssh keys
to your Virtual Machines.

.. Note:: We have not included these settings in the example ``config.yml``
          at the bottom of this page for security reasons. We do not want anyone
          copying the values we've used in our examples for security prone
          settings such as this. If you wish to set these yourself, you will
          need to manually add them to ``config.yml``.

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

More details can be found in the :ref:`registration` documentation.

Site root and static files
--------------------------

The site root, static root, and static url must also be set when configuring
|gwm|.

The ``SITE_ROOT`` is the subdirectory on the website:
``http://example.com/<SITE_ROOT>``. The current default is empty.

The ``STATIC_ROOT`` is the directory on the filesystem that |gwm|'s static
files will be placed when you run ``django-admin.py collectstatic``. The current
default is ``/opt/ganeti_webmgr/collected_static``.

``STATIC_URL`` is the full url where |gwm| will look when trying to obtain
static files. The default for this is currently ``/static`` which means it will
try looking at the same domain it is hosted on. For example if your hostname is
`www.yourwebsite.com` it will look for them at ``www.yourwebsite.com/static``.

A standard configuration, putting |gwm| at the root of the domain, might look
like this::

    SITE_ROOT: /web_admin
    STATIC_ROOT: /opt/ganeti_webmgr/collected_static
    STATIC_URL: www.yourwebsite.com/static

Haystack Search Settings
------------------------

Haystack is |gwm|'s way of performing search indexing. It currently has one
setting which you need to worry about.

``HAYSTACK_WHOOSH_PATH`` is the path to a location on the filesystem which |gwm|
will store the search index files. This location needs to be readable and
writable by whatever user is running |gwm|. Example users might be the apache
or nginx user, or whatever user you've set the |gwm| process to run as.

The default path for this setting is ``/opt/ganeti_webmgr/whoosh_index``.

An example of this setting might be::

    HAYSTACK_WHOOSH_PATH: /opt/ganeti_webmgr/whoosh_index

More details can be found in the :ref:`search <search>` documentation.

Other settings
--------------

``ITEMS_PER_PAGE`` is a setting allowing you to globally limit or extend the
number of items on a page listing things. This this currently defaults to ``15``
items per page, so your pages will have up to 15 VMs, clusters and node's listed
on a single page. You might adjust this to a lower value if you find that
loading a large number on a single page slows things down.

::

    ITEMS_PER_PAGE: 20

Set ``VNC_PROXY`` to the ``hostname:port`` pair of your VNCAuthProxy server.
The VNC AuthProxy does not need to run on the same server as Ganeti Web Manager.

::

    VNC_PROXY: "localhost:8888"

``LAZY_CACHE_REFRESH`` (milliseconds) is the fallback cache timer that is checked
when the object is instantiated. It defaults to 600000ms, or ten minutes.

::

    LAZY_CACHE_REFRESH: 600000

``RAPI_CONNECT_TIMEOUT`` is how long |gwm| will wait in seconds before timing
out when requesting data from the ganeti cluster.

::

    RAPI_CONNECT_TIMEOUT: 3

Sample configuration
--------------------

An annotated sample YAML configuration file is shown below:

.. literalinclude:: ../../../ganeti_webmgr/ganeti_web/settings/config.yml.dist
  :language: yaml
