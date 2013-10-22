.. _old_upgrading:

Deprecated: Upgrading
=====================

.. warning::
  This document is deprecated as of |gwm| version 0.11.

.. Note:: Please read the instructions fully before starting. The order of
          operations is important. The upgrade may fail if done out of order.

This guide will walk you through upgrading Ganeti Web Manager. Our
upgrade process uses
`South <http://south.aeracode.org/docs/>`_, a database
migration tool that will update your database.

#. Backup the database
#. Download the latest code
#. Save a copy of **settings.py**
#. Deploy code to your existing directory
#. Copy **settings.py** back into the directory

Follow the guide for your version.

Upgrading From Version 0.4
--------------------------

If you are upgrading from version 0.4 you will be required to convert
your installation to use South. Version 0.4 did not track the database
with South, so South must be informed that your installation is already
partially migrated. Read the `South
documentation <http://south.aeracode.org/docs/convertinganapp.html#converting-other-installations-and-servers>`_
for more information about converting apps.

#. Backup your database
#. `install
   python-django-south <http://south.aeracode.org/docs/installation.html>`_.
#. Add "south" to the list of **INSTALLED\_APPS** inside **settings.py**
#. Make sure you add any new settings to **settings.py** that are listed
   in `Settings Changes`_
#. Synchronize the database with **./manage.py syncdb**
   ::

       $ ./manage.py syncdb

       /usr/lib/pymodules/python2.6/registration/models.py:4: DeprecationWarning: the sha module is deprecated; use the hashlib module instead
         import sha
       Syncing...
       Creating table south_migrationhistory
       No fixtures found.

       Synced:
        > django.contrib.auth
        > django.contrib.admin
        > django.contrib.contenttypes
        > django.contrib.sessions
        > django.contrib.sites
        > registration
        > logs
        > object_permissions
        > south

       Not synced (use migrations):
        - ganeti
        - logs
       (use ./manage.py migrate to migrate these)

#. Convert the ganeti app to use South for future migrations.
   ::

       $ ./manage.py migrate ganeti 0001 --fake

       /usr/lib/pymodules/python2.6/registration/models.py:4: DeprecationWarning: the sha module is deprecated; use the hashlib module instead
         import sha
        - Soft matched migration 0001 to 0001_version_0_4.
       Running migrations for ganeti:
        - Migrating forwards to 0001_version_0_4.
        > ganeti:0001_version_0_4
          (faked)

#. Convert the logs app to use South for future migrations.
   ::

       $ ./manage.py migrate logs 0001 --fake

       /usr/lib/pymodules/python2.6/registration/models.py:4: DeprecationWarning: the sha module is deprecated; use the hashlib module instead
         import sha
        - Soft matched migration 0001 to 0001_version_0_4.
       Running migrations for logs:
        - Migrating forwards to 0001_version_0_4.
        > logs:0001_version_0_4
          (faked)

#. Run South migration
   ::

       $ ./manage.py migrate

       /usr/lib/pymodules/python2.6/registration/models.py:4: DeprecationWarning: the sha module is deprecated; use the hashlib module instead
         import sha
       Running migrations for ganeti:
        - Migrating forwards to 0002_version_0_5.
        > ganeti:0002_version_0_5
        - Loading initial data for ganeti.
       No fixtures found.
       Running migrations for logs:
       - Nothing to migrate.

Upgrading from >=0.5
--------------------

#. **Backup** your database

Pre-0.8
~~~~~~~

#. Run South migration.
   ::

       $ ./manage.py migrate

0.8 till 0.11
~~~~~~~~~~~~~

#. Delete ghost migrations while running migrations.
   ::

       $ ./manage.py migrate --delete-ghost-migrations

#. Update **settings.py** following the guide below

Settings Changes
----------------

The following settings have been added or changed. Please modify
**settings.py** with these new values.

Version 0.5
~~~~~~~~~~~

TESTING
^^^^^^^

::

    # XXX - Django sets DEBUG to False when running unittests.  They want to ensure
    # that you test as if it were a production environment.  Unfortunately we have
    # some models and other settings used only for testing.  We use the TESTING flag
    # to enable or disable these items.
    #
    # If you run the unittests without this set to TRUE, you will get many errors!
    TESTING = False

ITEMS\_PER\_PAGE
^^^^^^^^^^^^^^^^

::

    # default items per page
    ITEMS_PER_PAGE = 20

VNC\_PROXY
^^^^^^^^^^

::

    # Enable the VNC proxy.  When enabled this will use the proxy to create local
    # ports that are forwarded to the virtual machines.  It allows you to control
    # access to the VNC servers.  When disabled, the console tab will connect
    # directly to the VNC server running on the virtual machine.
    #
    # Expected values: False if no proxy, string with proxy host and port otherwise
    # String syntax: "HOST:PORT", for example: "localhost:8888"
    #
    # Note: you will probably have to open more ports in firewall. For proxy's default
    # settings, it uses port 8888 for listening for requests and ports 7000..8000
    # for serving proxy.
    #
    # To run proxy (in 'util' directory):
    #  $ python vncauthproxy.py --websockets
    # If you want to use encryption, then:
    #  $ python vncauthproxy.py --websockets --cert=FILE.pem
    VNC_PROXY=False

Messages Framework
^^^^^^^^^^^^^^^^^^

-  Add **django.contrib.messages.middleware.MessageMiddleware** to
   **MIDDLEWARE\_CLASSES**
-  Add **django.contrib.messages** to **INSTALLED\_APPS** after
   **django.contrib.contenttypes**

Version 0.6
~~~~~~~~~~~

Rename Logs App
^^^^^^^^^^^^^^^

The **logs** app has been renamed
`object\_log <http://code.osuosl.org/projects/django-object-log>`_.
Update **INSTALLED\_APPS** to reflect this change.

Version 0.7
~~~~~~~~~~~

South
^^^^^

::

    # Disable South during unittests.  This is optional, but will likely cause unittests
    # to fail if these are not set properly.
    SOUTH_TESTS_MIGRATE = False
    SKIP_SOUTH_TESTS = True

Haystack
^^^^^^^^

::

    # haystack search engine config
    HAYSTACK_SITECONF = 'search_sites'
    HAYSTACK_SEARCH_ENGINE = 'whoosh'
    HAYSTACK_WHOOSH_PATH = os.path.join(DOC_ROOT, 'whoosh_index')

Version 0.8
~~~~~~~~~~~

**Remember that it is absolutely critical to back up your database
before making any changes.**

User Registration
^^^^^^^^^^^^^^^^^

::

    # Whether users should be able to create their own accounts.
    # False if accounts can only be created by admins.
    ALLOW_OPEN_REGISTRATION = True

More documentation for registration can be found at :ref:`registration`.

Ganeti Version
--------------

Ganeti Web Manager version 0.8
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Users have experienced problems with Ganeti version 2.1, because it does
not support some of the new RAPI features available in version 0.8 of
Ganeti Web Manager. (see Issue `#8973 <http://code.osuosl.org/issues/8973>`_). To avoid these
problems, use GWM 0.8 with Ganeti version 2.4 or better.
