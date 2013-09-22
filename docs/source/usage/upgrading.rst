.. _upgrading:

Upgrading
=========

.. note::
  Please read the instructions fully before starting. The order of operations
  is important. The upgrade may fail if done out of order.

.. warning::
  This guide is intended for |gwm| in versions 0.11 and higher.  If you have
  older installation that you want to upgrade, please read carefully
  :ref:`old_upgrading` page.

This guide will walk you through upgrading Ganeti Web Manager. Our upgrade
process uses `South <http://south.aeracode.org/docs/>`_, a database migration
tool that will update your database.

1. Back up the database
2. Make sure newest |gwm| is available in OSUOSL repository at
   http://ftp.osuosl.org/pub/osl/ganeti-webmgr/
3. Run your :ref:`setup script <setup-script>` with ``-u ./gwm_venv`` argument.

Follow the guide for your version.

0.11 and later
--------------

Since 0.11, |gwm| uses :ref:`special setup script <setup-script>` for
installing and upgrading.

By using this script (and due to other major changes in |gwm| architecture),
you now have to use different management script.  It gets installed into
|gwm|'s virtual environment (``/path-to-venv/bin/gwm-manage.py``).

In order to upgrade your database run::

  $ gwm-manage.py migrate --delete-ghost-migrations


Updated settings
----------------

0.11
~~~~

All settings are now part of virtual environment and not installed with |gwm|
as a Python package.  Look inside ``/path-to-venv/config/gwm_config.py`` to see
all configuration options.
