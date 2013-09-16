.. _configuring:

Configuring
===========

.. todo::
   Go into details on what settings do in settings.py. This should
   probably stick to our specifics, and provide links to Django.
   Probably will want to reference specific sections of docs for
   settings (VNC).

Deploying a production server requires additional setup steps.


Required
--------

#. Change your **SECRET\_KEY** and **WEB\_MGR\_API\_KEY** to unique (and
   hopefully unguessable) strings in your ``end_user.py``.

   .. versionchanged:: 0.11.0
      You can now set **GWM_SECRET_KEY** and **GWM_API_KEY** environmental variables
      to set these values. By default, if none of these values are set, GWM will
      create a ``.secret/`` directory in the root of the project containing files
      with randomly generated values for these keys.


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
