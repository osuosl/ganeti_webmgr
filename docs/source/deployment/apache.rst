.. _apache:

=================
Apache + mod_wsgi
=================

Overview
========

Before beginning deploying |gwm| using Apache, read the following Django article
on `deploying Django with apache and mod_wsgi <https://docs.djangoproject.com/en/1.4/howto/deployment/wsgi/modwsgi/>`_.

To get |gwm| installed there are a few steps.

* Install Apache
* Configure/install ``mod_wsgi`` and other Apache modules
* Create the |gwm| VirtualHost

Configuration
-------------
Make sure you have mod_wsgi installed and enabled in Apache before beginning.

Next you want to create a vhost which will contain the Apache settings
that will point to our Django app. In the Apache config or ``<VirualHost>``
you will need at least the following:

.. _apache_conf:

.. literalinclude:: apache.conf
    :language: apache

``WSGIDaemonProcess``:
    ``processes`` should be set to the number of CPU cores available.
    ``threads`` is fine to be left at 1.
    ``python-path`` is adding our virtualenv's site packages and |gwm| to the
    python path before executing the wsgi app.
    More info on this particular directive can be found on the `mod_wsgi docs
    <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide#Delegation_To_Daemon_Process>`_.

``WSGIScriptAlias``:
    This is the base URL path that |gwm| will be served at. In this case its at
    ``/`` (the root url).

``Alias``:
    Defines where to find the static assets (css, js, images) for |gwm|. This
    lets Apache serve the static files instead of having Django do it.
    You can leave this as is unless you modified the ``end_user.py`` settings.

