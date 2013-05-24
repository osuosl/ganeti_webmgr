{% block content %}

  {% for vm in vm_queryset %}
    {{ vm.hostname }}  {{ vm.primary_node }}  {{ vm.secondary_node }}
  {% endfor %}

{% endblock %}
