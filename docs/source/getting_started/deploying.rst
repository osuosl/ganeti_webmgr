.. _deploying:

Deployment
==========

If you haven't already :ref:`configured <configuring>` |gwm|, now would
be a good time to do so.

Now that you have a |gwm| instance setup and configured, you will want
to deploy it to somewhere that can be accessed by a web browser.


.. _test-server:

Testing
-------

If you are just trying |gwm| out, run from your
:ref:`virtual environment <virtual-environment>`::

  $ gwm-manage.py runserver

Then open a web browser, and navigate to ``http://localhost:8000``::

  firefox http://localhost:8000


Apache + mod_wsgi
-----------------

Follow the django guide to `deploy with apache
<https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/>`_.  Here
is an example ``mod_wsgi`` file::

  import os
  import sys

  path = '/var/lib/django/ganeti_webmgr'

  # activate virtualenv
  activate_this = '%s/venv/bin/activate_this.py' % path
  execfile(activate_this, dict(__file__=activate_this))

  # add project to path
  if path not in sys.path:
  sys.path.append(path)

  # configure django environment
  os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

  import django.core.handlers.wsgi
  application = django.core.handlers.wsgi.WSGIHandler()


Virtualenv
~~~~~~~~~~

The virtual environment must be activated for use with ``mod_wsgi``.  This
is done by executing the ``activate_this`` script generated when a virtualenv
is created.  The following code should be in the ``django.wsgi`` file apache
is configured to use with::

  # activate virtual environment
  activate_this = '%s/venv/bin/activate_this.py' % "PATH_TO_GANETI_WEBMGR"
  execfile(activate_this, dict(__file__=activate_this))


Nginx
-----


Gunicorn
--------


uWSGI
-----
