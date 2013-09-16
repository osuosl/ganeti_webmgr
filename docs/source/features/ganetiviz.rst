.. _ganetiviz:

Ganetiviz
===========

Graphical Visualization of a ganeti cluster is now possible with the help of
**ganetiviz** app in GWM (should be packaged in the next GWM release, version 0.11). 
Ganetiviz uses the Cytoscape JS library to render network graphs, where ganeti
nodes are represented as vertices and failover directions are shown as edges.

The graph is interactive and has the following features-

#. When you click on a node, all the instances running on that node are shown.
#. Further, when you click on an instance an edge in the graph connecting 2 nodes is highlighted.
#. The edge points to the secondary node for that particular instance originating at the primary node.
#. All the 'running' instances are shown in green and all the '*_DOWN' instances are shown in red.
#. Additional instance information is shown in the bottom right corner and is 
   fetched on demand on clicking on an instance.


Visualizing a  luster via GWM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. navigate to Cluster detail page
#. click the *Visualize* button with an 'eye' on it.
#. ganetiviz - opens up and renders the appropriate cluster.



History
~~~~~~~
In the initial stages of development I wrote a blog post
 `blog
post <http://www.pranjalmittal.in/2013/07/google-summer-of-code-update-1.html>`_.
on Ganetiviz.
It might be a little outmoded now, but might help understand its evolution.


Improving ganetiviz
~~~~~~~~~~~~~~~~~~~

Since ganetiviz is a part of GWM; improving ganetiviz actually means improving GWM.
Developing for GWM can sometimes be tedious for front-end contributors who do not want
to concern themselves with running a live or virtual ganeti Ecluster with GWM every time for
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


