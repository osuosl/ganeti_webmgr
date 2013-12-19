.. _nginx:

=====
Nginx
=====

uWSGI
=====

Before you begin, it is adviced you read over the following uWSGI article on
`setting up Django with uWSGI and Nginx <https://uwsgi.readthedocs.org/en/latest/tutorials/Django_and_nginx.html>`_

Configuration
-------------

First you will want to install uWSGI to the virtualenv which is easily done
with the following commands::

    cd /path/to/ganeti_webmgr
    source venv/bin/activate
    pip install uwsgi

Once uWSGI is installed you should configure Nginx to handle serving our static
assets and proxy the rest to uWSGI. Here is a sample nginx virtual host:


.. _nginx_conf:

.. literalinclude:: nginx_site.conf
    :language: nginx

Finally you will want to configure uWSGI. Here is a sample uWSGI configuration
file that should properly work with GWM:

.. literalinclude:: uwsgi.ini
