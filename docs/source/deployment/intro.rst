.. _deployment:

===========
Development
===========

|gwm| supports various methods of deployment. By default Django ships with a
simple python web server for development purposes. If your just trying to get
|gwm| up and running, or you simply want to contribute to the project then using
the :ref:`development-server` is probably your best bet. Otherwise check out
:ref:`static-files`.

.. _development-server:

Development Server
----------------------

If you are just testing |gwm| out, run::

    $ python ganeti_webmgr/manage.py runserver

Then open a web browser, and navigate to
`http://localhost:8000`::

   firefox http://localhost:8000

.. Note:: This should only be used to *test*. This should never be used in a
          *production* environment.


.. _static-files:

============
Static Files
============

Django is not very good at serving static files like CSS and Javascript.
This is why we use web servers like Apache or Nginx. So we need to collect all
of our static files into a single directory. To do this from the project root
edit `ganeti_web/ganeti_web/settings/end_user.py` and update the `STATIC_ROOT`
value to be the full absolute path to a where you would like to collect all
the static assets at. After this run the following commands from the project root

::

    source venv/bin/activate
    python ganeti_webmgr/manage.py collectstatic

Once you've done that, you can move on to deploying using your prefered web server.

* :ref:`Apache <apache>`
* :ref:`Nginx <nginx>`