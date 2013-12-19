Console
=======

Ganeti Web Manager provides both graphical and serial console services
through a proxy.  Graphical console services are provided using `noVNC
<http://kanaka.github.io/noVNC/>`_, an HTML5 VNC client. noVNC
requires WebSockets to function. Support for older browsers is
provided through a flash applet that is used transparently in the
absence of WebSockets.  Serial console services are provided via
`jsTerm <http://jsterm.com/>`_, an HTML5 terminal emulator.

.. _consoleauthproxy:

Console Auth Proxy
------------------

.. REPLACE THIS IMAGE .. figure:: /_static/vnc1.png
   :align: center

   ..

.. RENAME TVAP to consoleauthproxy ..

`Console Auth Proxy
<http://code.osuosl.org/projects/twisted-vncauthproxy>`_ must be
installed and running to access graphical and serial console services.
The proxy allows secure access to Ganeti clusters located behind
firewalls, VPNs, or NATs.

.. REPLACE THIS IMAGE .. figure:: /_static/vnc2.png
   :align: center

   ..

The proxy has a control channel that is used to request port
forwarding to a specific virtual machine. It will respond with a local
port and temporary credentials that must be used within a short
period. This allows a secure connection with the proxy without
compromising the console credentials, and without leaving the port
open to anyone with a port scanner.

Configuring Console Auth Proxy
------------------------------

Set the host and port that the proxy uses in ``gwm_config.py`` with the
``CONSOLE_PROXY`` setting.

Syntax is ``HOST:CONTROL_PORT``, for example: ``"localhost:8888"``.

If the host is ``localhost``, the proxy will only be accessible to
clients and browsers on the same machine as the proxy. Production
servers should use a public hostname or IP.

.. note:: If :ref:`vagrant` is being used, the virtual machine's fully
.. qualified domain name and IP address must be added to the host's
.. ``/etc/hosts`` file.

::

    # located in your settings file
    CONSOLE_PROXY = 'localhost:8888'

Starting The Proxy Daemon
~~~~~~~~~~~~~~~~~~~~~~~~~

The proxy is started with twistd, the twisted daemon.  Eventually
init.d scripts will be included, but for now the daemon must be
started by hand.

::

    twistd --pidfile=/tmp/proxy.pid -n vncap

Starting Flash Policy Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Browsers that do not support WebSockets natively require the use of a
Flash applet on the proxy system.  Flash applets that use sockets must
retrieve a policy file from the host to which they are connecting.
The proxy includes a policy server, but it must be run separately and
with root privileges because the policy server runs on port 843, which
is a privileged port.  Firewalls may require port forwarding to work
with the Flash policy server.

::

    sudo twistd --pidfile=/tmp/policy.pid -n flashpolicy

Firewall Rules
~~~~~~~~~~~~~~

The following ports are used by default

-  **8888**: Control port used to request console forwarding. Should be open
   between **Ganeti Web Manager** and **Proxy**.
-  **12000+**: Internal console ports assigned by **Ganeti**. Should be open
   between **Proxy** and **Ganeti Nodes**.
-  **7000-8000**: External console ports assigned by **Proxy**. Should be
   open between **Proxy** and **Clients/Web Browsers**.
-  **843**: Flash policy server. Required to support browsers without
   native WebSocket support. Should be open between **Proxy** and
   **Clients/Web Browsers**.

Debugging Help
--------------

.. NB: Replace this with FAQ-style debugging hints?

Python path for Flash policy server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following error indicates that the Python path is not set or the
proxy is not installed::

  /usr/bin/twistd: Unknown command: flashpolicy

Ensure that the virtualenv is active::

  source venv/bin/activate

If not using a virtualenv, then the ``PYTHONPATH`` environment
variable must be set manually as root::

  export set PYTHONPATH=.
