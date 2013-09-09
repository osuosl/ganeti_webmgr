# Copyright (C) 2012 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

"""
Relatively pure functions for instantiating virtual machines from templates
and vice versa.

These only depend on Django's ORM and not on any of the view or form
machinery.
"""

from object_log.models import LogItem

from ganeti_web.caps import has_balloonmem
from jobs.models import Job
from virtualmachines.models import VirtualMachine
from vm_templates.models import VirtualMachineTemplate

log_action = LogItem.objects.log_action


def instance_to_template(vm, name):
    """
    Create, save, and return a VM template representing all of the information
    in the VM instance.

    The name is given to the template to distinguish it from other templates.
    """

    template = VirtualMachineTemplate()

    # Basic stuff first.
    template.template_name = name
    template.description = ""
    template.cluster = vm.cluster
    template.start = vm.info["admin_state"]
    template.disk_template = vm.info["disk_template"]
    template.os = vm.operating_system

    # Backend parameters.
    template.vcpus = vm.virtual_cpus
    template.memory = vm.ram
    if has_balloonmem(vm.cluster):
        template.minmem = vm.minram
    template.disks = [{"size": size} for size in vm.info["disk.sizes"]]
    template.disk_type = vm.info["hvparams"]["disk_type"]
    template.nics = [{"mode": mode, "link": link}
                     for mode, link in zip(vm.info["nic.modes"],
                                           vm.info["nic.links"])]
    template.nic_type = vm.info["hvparams"]["nic_type"]

    # Hypervisor parameters.
    template.kernel_path = vm.info["hvparams"]["kernel_path"]
    template.root_path = vm.info["hvparams"]["root_path"]
    template.serial_console = vm.info["hvparams"]["serial_console"]
    template.boot_order = vm.info["hvparams"]["boot_order"]
    template.cdrom_image_path = vm.info["hvparams"]["cdrom_image_path"]
    template.cdrom2_image_path = vm.info["hvparams"]["cdrom2_image_path"]

    template.save()

    return template


def template_to_instance(template, hostname, owner):
    """
    Instantiate a VM template with a given hostname and owner.
    """

    cluster = template.cluster
    beparams = {
        "vcpus": template.vcpus,
    }

    hvparams = {}
    hv = template.hypervisor
    kvm = hv == 'kvm'
    pvm = hv == 'xen-pvm'
    hvm = hv == 'xen-hvm'
    kvm_or_hvm = kvm or hvm
    kvm_or_pvm = kvm or pvm

    if kvm_or_hvm:
        hvparams.update(boot_order=template.boot_order)
        hvparams.update(cdrom_image_path=template.cdrom_image_path)
        hvparams.update(nic_type=template.nic_type)
        hvparams.update(disk_type=template.disk_type)
    if kvm_or_pvm:
        hvparams.update(kernel_path=template.kernel_path)
        hvparams.update(root_path=template.root_path)
    if kvm:
        hvparams.update(cdrom2_image_path=template.cdrom2_image_path)
        hvparams.update(serial_console=template.serial_console)

    memory = template.memory
    if has_balloonmem(cluster):
        minram = template.minmem
        beparams['minmem'] = minram
        beparams['maxmem'] = memory
    else:
        beparams['memory'] = memory

    vcpus = template.vcpus
    disk_size = template.disks[0]["size"]

    kwargs = {
        "os": template.os,
        "hypervisor": hv,
        "ip_check": template.ip_check,
        "name_check": template.name_check,
        "beparams": beparams,
        "no_install": template.no_install,
        "start": not template.no_start,
        "hvparams": hvparams,
    }

    # Using auto allocator
    if template.iallocator:
        default_iallocator = cluster.info['default_iallocator']
        kwargs.update(iallocator=default_iallocator)
    # Not using allocator, pass pnode
    else:
        kwargs.update(pnode=template.pnode)
        # Also pass in snode if it exists (drdb)
        if template.snode:
            kwargs.update(snode=template.snode)
        # secondary node isn't set but we're using drdb, so programming error
        # (this shouldn't happen if form validation is done correctly)
        elif template.disk_template == 'drdb':
            msg = 'Disk template set to drdb, but no secondary node set'
            raise RuntimeError(msg)

    job_id = cluster.rapi.CreateInstance('create', hostname,
                                         template.disk_template,
                                         template.disks, template.nics,
                                         **kwargs)
    vm = VirtualMachine()

    vm.cluster = cluster
    vm.hostname = hostname
    vm.ram = memory
    if has_balloonmem(cluster):
        vm.minram = minram
    vm.virtual_cpus = vcpus
    vm.disk_size = disk_size

    vm.owner = owner
    vm.ignore_cache = True

    # Do a dance to get the VM and the job referencing each other.
    vm.save()
    job = Job.objects.create(job_id=job_id, obj=vm, cluster=cluster)
    job.save()
    vm.last_job = job
    vm.save()

    # Grant admin permissions to the owner.
    owner.permissable.grant('admin', vm)

    return vm
