LDAP
====

.. versionadded:: 0.10

Ganeti Web Manager supports LDAP authentication through the use of
`django-auth-ldap`_ and `python-ldap`_. A fabric command has been
written to easily handle enabling and disabling LDAP support.

.. _ldap-dependencies:

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

      $ cd ganeti_webmgr/ganeti_web/settings
      $ cp ldap_settings.py.dist ldap_settings.py

#. Change `ldap_settings.py` to fit your LDAP configuration.

   ::

      $ vi ldap_settings.py

   .. note::
       ``ldap_settings.py.dist`` has been thoroughly commented so that external
       documentation shouldn't be needed. If you have specific questions about
       options or want an overview of the package, please consult the
       `django-auth-ldap`_ documentation.


#. Install the LDAP-specific requirements.

  ::

    $ pip install -r requirements/ldap.txt # in root of repository

Disabling
---------
If you would like to later disable LDAP support, all that is required is
to remove your ldap_settings file::

   $ cd ganeti_webmgr/ganeti_web/settings
   $ rm ldap_settings.py

.. note::
    This will not remove `django-auth-ldap`_ and `python-ldap`_, nor the
    the system specific dependencies. If you want to remove these, use pip
    and your system's package manager.

.. _python-ldap: http://www.python-ldap.org/doc/html/index.html
.. _django-auth-ldap: http://pythonhosted.org/django-auth-ldap/
