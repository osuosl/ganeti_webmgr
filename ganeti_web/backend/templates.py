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

from ganeti_web.models import Job, VirtualMachine, VirtualMachineTemplate

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
    memory = template.memory
    vcpus = template.vcpus
    disk_size = template.disks[0]["size"]

    beparams = {
        "memory": memory,
        "vcpus": template.vcpus,
    }

    kwargs = {
        "os": template.os,
        "ip_check": template.ip_check,
        "name_check": template.name_check,
        "pnode": template.pnode,
        "beparams": beparams,
    }

    job_id = cluster.rapi.CreateInstance('create', hostname,
                                         template.disk_template,
                                         template.disks, template.nics,
                                         **kwargs)
    vm = VirtualMachine()

    vm.cluster = cluster
    vm.hostname = hostname
    vm.ram = memory
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
    log_action('CREATE', owner, vm)

    return vm
