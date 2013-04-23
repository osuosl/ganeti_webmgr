from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2.utils import A

from ganeti_web.templatetags.webmgr_tags import (render_storage, render_os,
                                                 abbreviate_fqdn)


class BaseVMTable(tables.Table):

    # bulk = tables.CheckBoxColumn(accessor="pk", attrs={'name': 'bulk[]'})
    status = tables.TemplateColumn(
        template_name="ganeti/virtual_machine/vmfield_status.html",
    )
    hostname = tables.LinkColumn(
        "instance-detail",
        kwargs={"cluster_slug": A("cluster.slug"),
                "instance": A("hostname")},
        verbose_name='name',
    )
    owner = tables.LinkColumn(
        "user-detail-name",
        args=[A("owner")],
    )
    primary_node = tables.Column(verbose_name='node')
    operating_system = tables.Column(verbose_name='OS')
    ram = tables.Column(verbose_name='RAM')
    disk_size = tables.Column(verbose_name='disk space')
    virtual_cpus = tables.Column(verbose_name='vCPUs')

    class Meta:
        sequence = ("status", "hostname", "...")
        order_by = ("hostname")

    def __init__(self, *args, **kwargs):
        self.template = "table.html"
        return super(BaseVMTable, self).__init__(*args, **kwargs)

    def render_disk_size(self, value):
        return render_storage(value)

    def render_ram(self, value):
        return render_storage(value)

    def render_operating_system(self, value):
        return render_os(value)

    def render_primary_node(self, value):
        return abbreviate_fqdn(value)


class VMTable(BaseVMTable):

    # This may look weird, but the VirtualMachine View shows clusters, but the
    # cluster view does not, which is why it isn't in the base table.
    cluster = tables.Column()

    class Meta:
        sequence = ("status", "hostname", "cluster", "...")
        order_by = ("hostname")

    # TODO: Make this into its own column type
    def render_cluster(self, value, record):
        text = abbreviate_fqdn(value)
        if not self.can_create:  # no perms, dont make it a link.
            return text
        kwargs = {"cluster_slug": record.cluster.slug}
        url = reverse("cluster-detail", kwargs=kwargs)
        html = '<a href="{link}">{text}</a>'.format(link=url, text=text)
        return mark_safe(html)
