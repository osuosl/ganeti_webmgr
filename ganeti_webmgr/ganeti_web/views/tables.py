from django.utils.safestring import mark_safe

from django_tables2 import (Table, Column, LinkColumn, TemplateColumn,
                            DateTimeColumn)
from django_tables2.utils import A

from ..templatetags.webmgr_tags import (render_storage, render_os,
                                        abbreviate_fqdn, format_job_op)

from utils import hv_prettify


class BaseTable(Table):
    def __init__(self, *args, **kwargs):
        kwargs['template'] = kwargs.get("template", "table.html")
        return super(BaseTable, self).__init__(*args, **kwargs)


class BaseVMTable(BaseTable):

    status = TemplateColumn(
        template_name="ganeti/virtual_machine/vmfield_status.html",
        attrs={"th": {"class": "status_indicator"}}
    )
    cluster = LinkColumn(
        "cluster-detail",
        args=[A("cluster.slug")],
        accessor="cluster.slug",
        verbose_name='cluster'
    )
    hostname = LinkColumn(
        "instance-detail",
        kwargs={"cluster_slug": A("cluster.slug"),
                "instance": A("hostname")},
        verbose_name='name',
    )
    owner = Column()
    node = Column(verbose_name='node', accessor="primary_node")
    operating_system = Column(verbose_name='OS')
    ram = Column(verbose_name='RAM')
    disk_size = Column(verbose_name='disk space')
    virtual_cpus = Column(verbose_name='vCPUs')

    class Meta:
        sequence = ("status", "hostname", "cluster", "...")
        order_by = ("hostname")
        empty_text = "No Virtual Machines"

    def render_disk_size(self, value):
        return render_storage(value)

    def render_ram(self, value):
        return render_storage(value)

    def render_operating_system(self, value):
        return render_os(value)

    def render_node(self, value):
        return abbreviate_fqdn(value)

    def render_owner(self, value):
        url = value.get_absolute_url()
        url_str = '<a href="{0}">{1}</a>'
        return mark_safe(url_str.format(url, value))


class VMTable(BaseVMTable):
    class Meta:
        sequence = ("status", "hostname", "cluster", "...")
        order_by = ("hostname")
        empty_text = "No Virtual Machines"


class ClusterVMTable(BaseVMTable):
    class Meta:
        exclude = ("cluster",)
        order_by = ("hostname")
        empty_text = "This cluster has no Virtual Machines"


class NodeVMTable(BaseVMTable):
    class Meta:
        exclude = ("cluster", "node")
        order_by = ("hostname")
        empty_text = ("This node has no Virtual Machines "
                      "assigned to it as this role.")


class VMTemplateTable(BaseTable):

    template_name = LinkColumn(
        "template-detail",
        args=[A("cluster.slug"), A("template_name")],
        verbose_name="name"
    )
    description = Column()
    cluster = LinkColumn(
        "cluster-detail",
        args=[A("cluster.slug")],
        accessor="cluster.slug",
        verbose_name="cluster"
    )
    os = Column(verbose_name='OS')
    memory = Column(verbose_name='RAM')
    disk_space = Column()
    vcpus = Column(verbose_name='vCPUs')

    class Meta:
        sequence = ("template_name", "description", "cluster", "os", "memory",
                    "disk_space", "vcpus")
        order_by = ("template_name")
        empty_text = "No Templates"

    def render_os(self, value):
        return render_os(value)

    def render_memory(self, value):
        return render_storage(value)

    def render_disk_space(self, value):
        return render_storage(value)


class ClusterTable(BaseTable):

    cluster = LinkColumn(
        "cluster-detail",
        args=[A("slug")],
        accessor="slug",
        verbose_name='cluster'
    )
    description = Column()
    version = Column(
        accessor="info.software_version",
        orderable=False,
        default="unknown"
    )
    hypervisor = Column(
        accessor="info.default_hypervisor",
        orderable=False,
        default="unknown"
    )
    master_node = LinkColumn(
        "node-detail",
        kwargs={"cluster_slug": A("slug"),
                "host": A("info.master")},
        accessor="info.master",
        orderable=False,
        default="unknown"
    )
    nodes = Column(accessor="nodes.count", orderable=False)
    vms = Column(accessor="virtual_machines.count", verbose_name='VMs',
                 orderable=False)

    class Meta:
        empty_text = "No Clusters"
        sequence = ("cluster", "description", "version", "hypervisor",
                    "master_node", "nodes", "vms")
        order_by = ("cluster")

    def render_hypervisor(self, value):
        return hv_prettify(value)


class JobTable(BaseTable):
    job_id = LinkColumn(
        'job-detail',
        args=[A("cluster.slug"), A("job_id")]
    )
    cluster = LinkColumn(
        "cluster-detail",
        args=[A("cluster.slug")],
        accessor="cluster.slug",
        verbose_name='cluster'
    )
    object = TemplateColumn(
        template_name="ganeti/overview/object_link.html",
        accessor="obj",
        orderable=False  # Cannot access generic fk to get obj name for sort
    )
    operation = Column(accessor="op", verbose_name="operation")
    # Extra space is because it doesn't like the word status for some reason.
    status = Column(verbose_name="status ")
    finished = DateTimeColumn()

    class Meta:
        empty_text = "No jobs"
        order_by = ("job_id")

    def render_operation(self, value):
        return format_job_op(value)


class ClusterJobTable(JobTable):

    class Meta:
        exclude = ("cluster",)
        empty_text = "No jobs available for this cluster"
