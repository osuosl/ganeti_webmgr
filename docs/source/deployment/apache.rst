.. _apache:

=================
Apache + mod_wsgi
=================

Overview
========

Before beginning deploying |gwm| using Apache, read the following Django article
on `deploying Django with apache and mod_wsgi <https://docs.djangoproject.com/en/1.4/howto/deployment/wsgi/modwsgi/>`_.

If you haven't already, make sure you've set up :ref:`static-files`.

To get |gwm| installed there are a few steps.

* Install Apache
* Configure/install ``mod_wsgi`` and other Apache modules
* Create the |gwm| VirtualHost

Configuration
-------------
Make sure you have mod_wsgi installed and enabled in Apache before beginning.

Next you want to create a vhost which will contain the Apache settings that will
point to our Django app. The following is an example which assumes you have
installed |gwm| to the default location in ``/opt/ganeti_webmgr``, and that your
running python 2.6. Replace the locations with where you've actually installed
it to, and replace python2.6 with the version of python you're using.

The following is an example Apache configuration for Apache 2.4:

.. _apache24_conf:

.. literalinclude:: apache24.conf
    :language: apache

If you're running an older version of Apache, ``Require all granted`` isn't
supported, so you'll need to do the following:

.. _apache22_conf:

.. literalinclude:: apache22.conf
    :language: apache

``WSGIDaemonProcess``:
    ``processes`` should be set to the number of CPU cores available.

    ``threads`` is fine to be left at 1.

    ``python-path`` is adding our installation containing |gwm| to the
                    pythonpath so it, and all of the dependencies installed can
                    be accessed by mod_wsgi.

                    More info on this particular directive can be found on the
                    `mod_wsgi docs
                    <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide#Delegation_To_Daemon_Process>`_.

``WSGIScriptAlias``:
    This is the base URL path that |gwm| will be served at. In this case its at
    ``/`` (the root url).

``Alias``:
    Defines where to find the static assets (css, js, images) for |gwm|. This
    lets Apache serve the static files instead of having Django do it.
    You can leave this as is unless you modified the ``STATIC_ROOT`` setting
    in your config file.

