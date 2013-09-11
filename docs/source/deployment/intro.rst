.. _deployment:

=====
Intro
=====

|gwm| supports various methods of deployment. By default Django ships with a
simple python web server for development purposes. If your just trying to get
|gwm| up and running, or you simply want to contribute to the project then using
the :ref:`test-server` is probably your best bet.

.. _development-server:

The Development Server
----------------------

If you are just testing |gwm| out, run::

    $ python ganeti_web/manage.py runserver

Then open a web browser, and navigate to
`http://localhost:8000`::

   firefox http://localhost:8000

.. Note:: This should only be used to *test*. This should never be used in a
          *production* environment.

Deployment
----------

If you want to deploy using Apache or Nginx just follow the instructions for
your web server of choice:

* :ref:`Apache <apache>`
* :ref:`Nginx <nginx>`