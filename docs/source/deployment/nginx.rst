.. _nginx:

=============
Nginx + uWSGI
=============

uWSGI
=====

Before you begin, it is adviced you read over the following uWSGI article on
`setting up Django with uWSGI and Nginx <https://uwsgi.readthedocs.org/en/latest/tutorials/Django_and_nginx.html>`_

If you haven't already, make sure you've set up :ref:`static-files`.

Configuration
-------------

First you will want to install uWSGI to the virtualenv which is easily done
with the following commands::

    $ source /opt/ganeti_webmgr/bin/activate
    $ pip install uwsgi

Once uWSGI is installed you should configure Nginx to handle serving our static
assets and proxy the rest to uWSGI. This assumes you've already collected
static files to the default location. Here is a sample nginx virtual host:


.. _nginx_conf:

.. literalinclude:: nginx_site.conf
    :language: nginx

Finally you will want to configure uWSGI. Here is a sample uWSGI configuration
file that should properly work with GWM:

.. literalinclude:: uwsgi.ini

To start uwsgi you can run the following command, pointing it at your uwsgi file::

    $ uwsgi --ini /path/to/gwm_uwsgi.ini