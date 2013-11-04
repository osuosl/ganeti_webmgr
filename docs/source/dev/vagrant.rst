.. _vagrant:

Vagrant
--------

`Vagrant <http://www.vagrantup.com/>`_ is a tool to help automate the creation
and deployment of virtual machines for development purposes. It reduces the
amount of effort to make sure multiple developers are using the same set of
tools to reduce complaints of "but it worked on my machine".

|gwm| comes with a Vagrantfile and uses Chef to automate the deployment process
within Vagrant.

Use
~~~

Using Vagrant to deploy |gwm| is simple. You will need Vagrant version **1.3.0**
or greater and two vagrant plugins, `vagrant-berkshelf` and `vagrant-omnibus`.

`Installing  Vagrant`_ is easy, you can install it to your system by downloading
the appropriate package, and running it.

To install the `vagrant-berkshelf`_ and `vagrant-omnibus`_ plugins run the following
command in your terminal::

    vagrant-plugin install vagrant-berkshelf
    vagrant-plugin install vagrant-omnibus

Configuration
~~~~~~~~~~~~~

Configuration of the deployment with Vagrant is done using `Chef`_.  For
documentation on the available attributes for configuring the deployment visit
the cookbook's github here: https://github.com/osuosl-cookbooks/ganeti_webmgr_cookbook


.. _Installing Vagrant:  http://docs.vagrantup.com/v2/installation/index.html
.. _vagrant-berkshelf: https://github.com/riotgames/vagrant-berkshelf
.. _vagrant-omnibus: https://github.com/schisamo/vagrant-omnibus
.. _Chef: http://www.opscode.com/chef/
