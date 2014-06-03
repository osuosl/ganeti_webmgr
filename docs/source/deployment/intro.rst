.. _deployment:

================
Deployment Intro
================

|gwm| supports various methods of deployment. By default Django ships with a
simple python web server for development purposes. If your just trying to get
|gwm| up and running, or you simply want to contribute to the project then using
the :ref:`development-server` is probably your best bet. Otherwise check out
:ref:`static-files`. Once you've gotten your static files figured out, move into
either deployment with :ref:`apache` or :ref:`nginx`.

.. _development-server:

Development Server
------------------

Make sure you've already checked out :ref:`initializing`.

If you are just testing |gwm| out, run::

    $ django-admin.py runserver

Then open a web browser, and navigate to `http://localhost:8000`.

If you want this to be accessable from a machine other than where you ran that
command, then run the following::

    $ django-admin.py runserver 0.0.0.0:8000

.. Note:: This should only be used to *test*. This should never be used in a
          *production* environment.


.. _static-files:

============
Static Files
============

Django is not very good at serving static files like CSS and Javascript.
This is why we use web servers like Apache or Nginx. So we need to collect all
of our static files into a single directory.

To adjust where these static assets get copied to, you can adjust the
``STATIC_ROOT`` setting in ``config.yml``. By default it copies files to
``/opt/ganeti_webmgr/collected_static``. To actual do the copy, run the following::

    $ source /opt/ganeti_webgr/bin/activate
    $ django-admin.py collectstatic

Once you've done that, you can move on to deploying using your prefered web server.

* :ref:`Apache <apache>`
* :ref:`Nginx <nginx>`
