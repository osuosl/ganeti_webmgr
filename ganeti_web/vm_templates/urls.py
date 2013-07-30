from django.conf.urls.defaults import patterns, url
from .views import (TemplateFromVMInstanceView, VMInstanceFromTemplateView,
                    TemplateListView)

from virtualmachines.forms import vm_wizard
from virtualmachines.urls import vm_prefix
from clusters.urls import cluster

template = '(?P<template>[^/]+)'
template_prefix = '%s/template/%s' % (cluster, template)


urlpatterns = patterns(
    'vm_templates.views',

    url(r'^templates/$', TemplateListView.as_view(), name='template-list'),

    url(r'^template/create/$',
        vm_wizard(initial_dict={0: {'choices': [u'template_name']}}),
        name='template-create'),

    url(r'^%s/?$' % template_prefix, 'detail', name='template-detail'),

    url(r'^%s/delete/?$' % template_prefix, 'delete', name='template-delete'),

    url(r'^%s/edit/?$' % template_prefix, vm_wizard(), name='template-edit'),

    url(r'^%s/copy/?$' % template_prefix, 'copy', name='template-copy'),

    url(r'^%s/vm/?$' % template_prefix, VMInstanceFromTemplateView.as_view(),
        name='instance-create-from-template'),

    url(r'^%s/template/?$' % vm_prefix, TemplateFromVMInstanceView.as_view(),
        name='template-create-from-instance'),
)
