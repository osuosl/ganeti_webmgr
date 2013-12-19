.. _compatibility:

Compatibility
-------------

Ganeti Web Manager is compatible with the following:

**Ganeti**
  Supported versions: **2.4.x--2.6.0**.

  Any newer software should work, but its features may not be implemented in
  |gwm|.

  .. warning::
    Earlier versions are unsupported; they may occasionally work, but
    should not be relied upon.


**Browsers**
  `Mozilla Firefox`_ >= 3.x, current `Google Chrome`_/`Google Chromium`_.

  Other contemporary browsers may also work, but are not supported.

  The web-based console requires browser support of WebSockets and
  HTML5.


**Databases**
  `SQLite`_, `MySQL`_.

  .. versionadded:: 0.10
    `PostgreSQL`_ has limited support

.. _compatible-operating-systems:

**Operating Systems**
  Ubuntu 11.10, Ubuntu 12.04, CentOS 6.

  Known to work on Debian 7 and CentOS 5.

  Debian 6 should work, provided that pip and virtualenv are the latest
  version.

.. _Ganeti: http://code.google.com/p/ganeti/
.. _Mozilla Firefox: http://mozilla.com/firefox
.. _Google Chrome: http://www.google.com/chrome/
.. _Google Chromium: http://www.chromium.org/
.. _SQLite: https://sqlite.org/
.. _MySQL: https://www.mysql.com/
.. _PostgreSQL: http://postgresql.com/
