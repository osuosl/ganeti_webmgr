{% block content %}

var CLR = {
  branch:"#b2b19d",
  ganetinode:"orange",
  ganetivm:"#922E00",
  ganetinodegroup:"#a7af00"
}
<br/>
<br/>

{# Defining the vertices of the Ganeti Graph and not really the Ganetinodes #}
var GanetiNodes = {{ graph_nodes }}
<br/>
<br/>
{# Defining the edges of the Ganeti Cluster Graph. #}
var GanetiEdges = {{ graph_edges }}
<br/>
{% endblock %}
