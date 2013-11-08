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

Once you have **node1** running, you can add it to |gwm| by using the `add
cluster` button on the cluster page. The username and password are both vagrant,
which will let you communicate with the cluster.


