.. _configuring:

Configuring
===========

.. todo::
   Go into details on what settings do in settings.py. This should
   probably stick to our specifics, and provide links to Django.
   Probably will want to reference specific sections of docs for
   settings (VNC).

Deploying a production server requires additional setup steps.

Helper Functions
----------------

.. versionadded:: 0.11.0

.. Note:: These functions are only available in ``end_user.py``

There a few helper functions that have been added to |gwm| settings to help with
getting full paths to files relative to |gwm|.

:func:`root` is a function which will return an absolute path where the arguments
given are joined together with the path to the root of the project. Similarly,
:func:`app_root` will return the absoulte path relative to the app directory of GWM.
(Where different Django apps are. By default this is the ganeti_web folder).

These are useful if you need to add or change the CSS and/or templates of GWM.
For most cases, you will not need to use these, but they are available if you do.

Examples::

  root('some', 'path') # Will return /path/to/ganeti_webmgr/some/path
  app_root('arbitrary', 'test', 'path') # Will return /path/to/ganeti_webmgr/ganeti_web/arbitrary/test/path


There are also some helpers available to retrieve setting values from
environmental variables or files containing the secrets.

:func:`get_env_or_file_secret` can be used to retrieve a setting from an
environmental variable and will fall back to checking for the value in a file.
It will return None if it finds neither.
:func:`get_env_or_file_or_create` does the same thing as the previous function,
however it will create the file and generate a random secret if the file
doesn't exist.

Examples::

  # Will grab the value from the environmental variable `DB_NAME`
  # if its empty, will read the value from `DB_NAME.txt`.
  get_env_or_file_secret('DB_NAME', '~/.secrets/DB_NAME.txt')

  # Same as above but creates `DB_NAME.txt` if it doesn't exist.
  get_env_or_file_secret_or_create('DB_NAME', '~/.secrets/DB_NAME.txt')


Required
--------

#. Change your **SECRET\_KEY** and **WEB\_MGR\_API\_KEY** to unique (and
   hopefully unguessable) strings in your ``end_user.py``.

   .. versionadded:: 0.11.0
      You can now set **GWM_SECRET_KEY** and **GWM_API_KEY** environmental variables
      to set these values. By default, if these are not set, GWM will
      create a ``.secret/`` directory in the root of the project containing files
      with randomly generated values for these keys. If you wish to set the value
      in the files, simply create files with the names API_KEY.txt and SECREY_KEY.txt
      with the contents. You can continue to set these in ``end_user.py`` as well.

  .. Note:: **SECRET_KEY** must be set to a 16, 24, or 32 bit value.


#. Change the ownership of the ``whoosh_index`` directory to the user running
   the web server. If your using apache this will be either apache, or httpd.
   For nginx, the user will be nginx. Example::

       chown apache:apache whoosh_index/

#. Ensure the server has the ability to send emails or you have access
   to an SMTP server. Set **EMAIL_HOST**, **EMAIL_PORT**, and
   **DEFAULT_FROM_EMAIL** in ``end_user.py``. For more complicated
   outgoing mail setups, please refer to the `django email
   documentation <http://docs.djangoproject.com/en/dev/topics/email/>`_.

#. Configure the `Django Cache
   Framework <http://docs.djangoproject.com/en/dev/topics/cache/>`_ to
   use a production capable backend in ``end_user.py``. By default
   Ganeti Web Manager is configured to use the **LocMemCache** but it is
   not recommended for production. Use Memcached or a similar backend.

   ::

       CACHES = {
           'default': {
               'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
           }
       }


Optional
--------

VNC
---

#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   ``end_user.py``. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.

   ::

       VNC_PROXY = 'my.server.org:8888'

SSH Keys
--------
