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
var GanetiNodes = { <br/>
  {% for node,instances in nodedict.items %}
    "{{ node }}":{color:CLR.ganetinode, shape:"dot", alpha:1},
    <br/>
    {% for instance in instances %}
        "{{ instance }}":{color:CLR.ganetivm, alpha:0},
    {% endfor %}
    <br/>
  {% endfor %}
}
<br/>
<br/>

{# Defining the edges of the Ganeti Cluster Graph. #}
  {% for node,instances in nodedict.items %}
    "{{ node }}":
    {% for instance in instances %}
      "{{ instance }}":{length:6},
      {# Edges to Secondary Nodes #}
      {% for snode,slinkweight in psdict.node %}
          "{{ snode }}":{ length:15, width: {{ slinkweight }} },
      {% endfor %}
      }
    <br/>
    {% endfor %}
  {% endfor %}

{% endblock %}
