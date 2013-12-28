from django.conf.urls.defaults import patterns, url
from .views import VMDeleteView, VMListView

from clusters.urls import cluster
instance = '(?P<instance>[^/]+)'
vm_prefix = '%s/%s' % (cluster, instance)

urlpatterns = patterns(
    'virtualmachines.views',

    url(r'^vms/$', VMListView.as_view(), name="virtualmachine-list"),

    url(r'^%s/?$' % vm_prefix, 'detail', name="instance-detail"),

    url(r'^vm/(?P<id>\d+)/jobs/status/?$', 'job_status',
        name="instance-job-status"),

    url(r'^%s/users/?$' % vm_prefix, 'users', name="vm-users"),

    url(r'^%s/permissions/?$' % vm_prefix, 'permissions',
        name="vm-permissions"),

    url(r'^%s/permissions/user/(?P<user_id>\d+)/?$' % vm_prefix, 'permissions',
        name="vm-permissions-user"),

    url(r'^%s/permissions/group/(?P<group_id>\d+)/?$' % vm_prefix,
        'permissions', name="vm-permissions-user"),

    url(r'^%s/vnc/?$' % vm_prefix, 'novnc', name="instance-vnc"),

    url(r'^%s/ssh/?$' % vm_prefix, 'jsterm', name="instance-ssh"),

    url(r'^%s/vnc/popout/?$' % vm_prefix, 'novnc',
        {'template': 'ganeti/virtual_machine/vnc_popout.html'},
        name="instance-vnc-popout"),

    url(r'^%s/ssh/popout/?$' % vm_prefix, 'jsterm',
        {'template': 'ganeti/virtual_machine/ssh_popout.html'},
        name="instance-ssh-popout"),

    url(r'^%s/vnc_proxy/?$' % vm_prefix, 'vnc_proxy',
        name="instance-vnc-proxy"),

    url(r'^%s/ssh_proxy/?$' % vm_prefix, 'ssh_proxy',
        name="instance-ssh-proxy"),

    url(r'^%s/shutdown/?$' % vm_prefix, 'shutdown', name="instance-shutdown"),

    url(r'^%s/shutdown-now/?$' % vm_prefix, 'shutdown_now',
        name="instance-shutdown-now"),

    url(r'^%s/startup/?$' % vm_prefix, 'startup', name="instance-startup"),

    url(r'^%s/reboot/?$' % vm_prefix, 'reboot', name="instance-reboot"),

    url(r'^%s/migrate/?$' % vm_prefix, 'migrate', name="instance-migrate"),

    url(r'^%s/replace_disks/?$' % vm_prefix, 'replace_disks',
        name="instance-replace-disks"),

    url(r"^%s/delete/?$" % vm_prefix, VMDeleteView.as_view(),
        name="instance-delete"),

    url(r"^%s/reinstall/?$" % vm_prefix, "reinstall",
        name="instance-reinstall"),

    url(r"^%s/edit/?$" % vm_prefix, "modify", name="instance-modify"),

    url(r'^%s/edit/confirm/?$' % vm_prefix, "modify_confirm",
        name="instance-modify-confirm"),

    url(r"^%s/rename/?$" % vm_prefix, "rename", name="instance-rename"),

    url(r"^%s/reparent/?$" % vm_prefix, "reparent", name="instance-reparent"),

    url(r'^%s/keys/(?P<api_key>[^/]+)/?$' % vm_prefix, "ssh_keys",
        name="instance-keys"),

    url(r'^%s/object_log/?$' % vm_prefix, 'object_log', name="vm-object_log"),
)
