LDAP
====

.. versionadded:: 0.10

Ganeti Web Manager support LDAP authentication through the use of
`django-auth-ldap`_ and `python-ldap`_. A fabric command has been
written to easily handling enabling and disabling LDAP support.

Dependencies
------------

In order to use `python-ldap`_ a couple of system level packages need to
be installed first.

For a Debian based systems:
 * libldap2-dev 
 * libsasl2-dev

For a Red Hat based systems:
 * openldap-devel

Deploying
---------

To deploy Ganeti Web Manager with LDAP

#. Copy ``ldap_settings.py.dist`` to ``ldap_settings.py``.

   ::

      $ cp ldap_settings.py.dist ldap_settings.py

#. Change `ldap_settings.py` to fit your LDAP configuration.

   ::

      $ vi ldap_settings.py

.. note:: 
    ``ldap_settings.py.dist`` has been thoroughly commented so that external
    documentation shouldn't be needed. If you have specific questions about
    options or want an overview of the package, please consult the
    `django-auth-ldap`_ documentation.


#. Run the fabric command to enable LDAP in settings::

   $ fab ldap

``fab ldap`` installs `django-auth-ldap`_ and `python-ldap`_ and takes
care of the commenting and uncommenting the lines in settings.py that
handle LDAP imports.

Disabling
---------
If you would like to later disable LDAP support, all that is required is
to run::

   $ fab ldap:disable

.. note::
    This will remove `django-auth-ldap`_ and `python-ldap`_ but will not
    remove the system specific dependencies.

.. _python-ldap: http://www.python-ldap.org/doc/html/index.html
.. _django-auth-ldap: http://pythonhosted.org/django-auth-ldap/
