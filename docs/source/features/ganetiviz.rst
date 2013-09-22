.. _ganetiviz:

Ganetiviz
=========

Graphical Visualization of a ganeti cluster is now possible with the help of
**ganetiviz** app in GWM (should be packaged in the next GWM release, version 0.11). 
Ganetiviz uses the Cytoscape JS library to render network graphs, where ganeti
nodes are represented as vertices and failover directions are shown as edges.

The graph is interactive and has the following features-

Features
~~~~~~~~

#. Nodes are represented as circles, which can host a number of primary instances,
   and mirror data for instances hosted on other secondary nodes.
#. Any node can play the role of both a primary node or a secondary node.
#. When you click on a node, all the instances running on that node are shown.
#. Further, when you click on an instance an edge in the graph connecting 2 nodes is highlighted.
#. The edge points to the secondary node for that particular instance originating at the primary node.
#. Edge thickness between the nodes gives and idea of the total number of failover
   possibilities existing between two nodes.
#. All the 'running' instances are shown in green and all the '*_DOWN' instances are shown in red.
   Instances "red" in color are not "running" and might require a failover.
#. Additional instance information is shown in the bottom right corner and is 
   fetched on demand on clicking on an instance.
#. Zoom In - Zoom Out using mouse scroll in any region by placing mouse-pointer there first.
#. Long-click & hold the graph at any point and pan it in any direction to shift the whole graph object
   or Pan by using arrow keys, or use the previous mouse method: longclick-hold-move
#. Select any node ans press the character "s" to see all the secondary instances for a given node.
#. Press the character "c" at any time to clear (actually hide) all the visible instances.
#. Press the character 'r' to reset the whole graph orientation as in the beginning.
#. Most of this important information is available easily pressing character the 'h' ie. help.


Visualizing a cluster via GWM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Navigate to Cluster detail page
#. Click the *Visualize* button with an 'eye' on it.
#. ganetiviz - opens up and renders the appropriate cluster.



History
~~~~~~~
In the initial stages of development I wrote a blog post
 `blog
post <http://www.pranjalmittal.in/2013/07/google-summer-of-code-update-1.html>`_.
on Ganetiviz.
It might be a little outmoded now, but might help understand its evolution.

The `ganetiviz-cytoscape <https://github.com/pramttl/ganaetiviz-cytoscape>`_. project was
initially created as a front end component for ganetiviz which was then ported to
`devganetiviz <https://github.com/pramttl/devganetiviz>`_. - a django application that
can be run outside GWM and ships with some mock data to get started contributing 
to GWM in seconds.


Improving ganetiviz
~~~~~~~~~~~~~~~~~~~

Since ganetiviz is a part of GWM; improving ganetiviz actually means improving GWM.
Developing for GWM can sometimes be tedious for front-end contributors who do not want
to concern themselves with running a live or virtual ganeti cluster with GWM every time for
development purposes.

Ganetiviz has sister projects that makes it possible for anyone to start contribute easily.


#. Front-End code contribution

For front end contribution you must refer to 
`devganetviz <https://github.com/pramttl/devganetiviz>`, a separate django
project that comes with batteries included (fixture data, etc), so you do not need
to run any physical or virtual server to add front-end features to ganetiviz.


#. For any contribution that changes JSON data avaiable to the front end component.
For changing the data returned by GWM to ganetiviz, it is important to run GWM
the standard way along with a Virtual or real cluster.
