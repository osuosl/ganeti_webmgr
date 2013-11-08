.. test_cluster:

Vagrant Test Cluster
====================

For development we use Vagrant to set up a Ganeti Cluster to test on.

Setup
~~~~~

The Vagrant Test cluster is not included with |gwm| and is a seperate
repository, that must be cloned::

    git clone https://github.com/osuosl/vagrant-ganeti

Once you've cloned the repository you can refer to its  `README
<https://github.com/osuosl/vagrant-ganeti>`_ for more details  on how to use it.

Basic Usage
~~~~~~~~~~~

The vagrant-ganeti project comes with a 3 Ganeti nodes which can be used for
testing deployment of VMs. You typically only need **1 node** unless your testing
multi-node operations.

- Bring up the first node you can run by typing ``vagrant up node1``.

- The other nodes can be brought up the same way, just swap out ``node1`` with
  ``node2`` or ``node3``.

You can also bring up every node by using just ``vagrant up``, however if you
do not have much RAM or your already running memory intensive programs, this
should be avoided.


Using with |gwm|
~~~~~~~~~~~~~~~~

Once you have ``node1`` running, you can add it to |gwm| by using the `add
cluster` button on the cluster page.

The hostname field should be filled in with will be the IP Address for the given
node, which can be found in the Vagrantfile. The *username* and *password* are
both **vagrant**, which will let you communicate with the cluster.

