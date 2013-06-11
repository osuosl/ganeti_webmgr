.. _dependencies:

Dependencies
------------

Base
~~~~

Python
    >= 2.5

Python-dev

   ::

       sudo apt-get install python-dev

.. Note:: Python-dev is required because some pip packages need it to
          build dependencies

Databases
~~~~~~~~~

All databases need their required python binding installed in order for
Django to connect. Please refer to Django database `documentation
<https://docs.djangoproject.com/en/1.4/topics/install/#get-your-database-running>`_
if you have any issues.

MySQL
    python-mysql

    ::

      pip install MySQL-python

PostgreSQL
    postgresql_psycopg2

    ::

      pip install psycopg2

LDAP
~~~~

LDAP dependencies can be found on the :ref:`ldap-dependencies` page.

Compatibility
-------------

Ganeti Web Manager is compatible with the following:

Ganeti 
    **2.4.x--2.6.0**.
    
    Earlier versions are unsupported; they may occasionally work, but
    should not be relied upon.

Browsers
    `Mozilla Firefox`_ >= 3.x, current `Google Chrome`_/`Google Chromium`_.

    Other contemporary browsers may also work, but are not supported.

    The web-based VNC console requires browser support of WebSockets and
    HTML5.

Databases
    `SQLite`_, `MySQL`_.

    .. versionadded:: 0.10
       PostgreSQL has limited support

Operating Systems 
    Ubuntu 11.10, Ubuntu 12.04, CentOS 6.
    
    Known to work on Debian 7 and CentOS 5.
    
    Debian 6 should work, provided that pip, virtualenv and fabric are
    the latest version managed through pip.

.. _Ganeti: http://code.google.com/p/ganeti/
.. _Mozilla Firefox: http://mozilla.com/firefox
.. _Google Chrome: http://www.google.com/chrome/
.. _Google Chromium: http://www.chromium.org/
.. _SQLite: https://sqlite.org/
.. _MySQL: https://www.mysql.com/


