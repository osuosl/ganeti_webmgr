.. _deploying:

==========
Deployment
==========

Now that you have a |project| instance setup you will want to deploy
it to somewhere that can be accessed by a web browser.

Testing
-------
If you are just testing |project| out, run::

    $ python manage.py runserver

in a terminal, open a web browser, and navigate to
`http://localhost:8000`.


Apache + mod_wsgi
-----------------

Virtualenv
~~~~~~~~~~

The virtual environment must be activated for use with mod\_wsgi. This
is done by executing the **activate\_this** script generated when a
virtualenv is created. The following code should be in the
**django.wsgi** file apache is configured to use.

::

    # activate virtual environment
    activate_this = '%s/bin/activate_this.py' % PATH_TO_GANETI_WEBMGR
    execfile(activate_this, dict(__file__=activate_this))

Nginx
-----


Gunicorn
--------


uWSGI
-----


.. |project| replace:: Ganeti Web Manager
