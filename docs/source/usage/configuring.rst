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
   hopefully unguessable) strings in your settings.py.


#. Change the ownership of the ``whoosh_index`` directory to apache

   ::

       chown apache:apache whoosh_index/

#. Ensure the server has the ability to send emails or you have access
   to an SMTP server. Set **``EMAIL_HOST``**, **``EMAIL_PORT``**, and
   **``DEFAULT_FROM_EMAIL``** in settings.py. For more complicated
   outgoing mail setups, please refer to the `django email
   documentation <http://docs.djangoproject.com/en/dev/topics/email/>`_.

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

Optional
--------

VNC
---

#. Set **VNC\_PROXY** to the hostname of your VNC AuthProxy server in
   **settings.py**. The VNC AuthProxy does not need to run on the same
   server as Ganeti Web Manager.

   ::

       VNC_PROXY = 'my.server.org:8888'

SSH Keys
--------
