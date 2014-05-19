import time
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django_fields.fields import PickleField

from utils.fields import LowerCaseCharField


class VirtualMachineTemplate(models.Model):
    """
    Virtual Machine Template holds all the values for the create virtual
    machine form so that they can automatically be used or edited by a user.
    """

    template_name = models.CharField(max_length=255, default="")
    temporary = models.BooleanField(verbose_name=_("Temporary"), default=False)
    description = models.CharField(max_length=255, default="")
    cluster = models.ForeignKey("clusters.Cluster", related_name="templates",
                                null=True, blank=True)
    start = models.BooleanField(verbose_name=_('Start up After Creation'),
                                default=True)
    no_install = models.BooleanField(verbose_name=_('Do not install OS'),
                                     default=False)
    ip_check = models.BooleanField(verbose_name=_("IP Check"), default=True)
    name_check = models.BooleanField(verbose_name=_('DNS Name Check'),
                                     default=True)
    iallocator = models.BooleanField(verbose_name=_('Automatic Allocation'),
                                     default=False)
    iallocator_hostname = LowerCaseCharField(max_length=255, blank=True)
    disk_template = models.CharField(verbose_name=_('Disk Template'),
                                     max_length=16)
    # XXX why aren't these FKs?
    pnode = models.CharField(verbose_name=_('Primary Node'), max_length=255,
                             default="")
    snode = models.CharField(verbose_name=_('Secondary Node'), max_length=255,
                             default="")
    os = models.CharField(verbose_name=_('Operating System'), max_length=255)

    # Backend parameters (BEPARAMS)
    vcpus = models.IntegerField(verbose_name=_('Virtual CPUs'),
                                validators=[MinValueValidator(1)], null=True,
                                blank=True)
    # XXX do we really want the minimum memory to be 100MiB? This isn't
    # strictly necessary AFAICT.
    memory = models.IntegerField(verbose_name=_('Memory'),
                                 validators=[MinValueValidator(100)],
                                 null=True, blank=True)
    minmem = models.IntegerField(verbose_name=_('Minimum Memory'),
                                 validators=[MinValueValidator(100)],
                                 null=True, blank=True)
    disks = PickleField(verbose_name=_('Disks'), null=True, blank=True)
    # XXX why isn't this an enum?
    disk_type = models.CharField(verbose_name=_('Disk Type'), max_length=255,
                                 default="")
    nics = PickleField(verbose_name=_('NICs'), null=True, blank=True)
    # XXX why isn't this an enum?
    nic_type = models.CharField(verbose_name=_('NIC Type'), max_length=255,
                                default="")
    hypervisor = models.CharField(verbose_name=_('Hyerpervisor'),
                                  max_length=255, default="")

    # Hypervisor parameters (HVPARAMS)
    kernel_path = models.CharField(verbose_name=_('Kernel Path'),
                                   max_length=255, default="", blank=True)
    root_path = models.CharField(verbose_name=_('Root Path'), max_length=255,
                                 default='/', blank=True)
    serial_console = models.BooleanField(
        verbose_name=_('Enable Serial Console'))
    boot_order = models.CharField(verbose_name=_('Boot Device'),
                                  max_length=255, default="")
    cdrom_image_path = models.CharField(verbose_name=_('CD-ROM Image Path'),
                                        max_length=512, blank=True)
    cdrom2_image_path = models.CharField(
        verbose_name=_('CD-ROM 2 Image Path'),
        max_length=512, blank=True)

    class Meta:
        unique_together = (("cluster", "template_name"),)

    def __unicode__(self):
        if self.temporary:
            return u'(temporary)'
        else:
            return self.template_name

    def set_name(self, name):
        """
        Set this template's name.

        If the name is blank, this template will become temporary and its name
        will be set to a unique timestamp.
        """

        if name:
            self.template_name = name
        else:
            # The template is temporary and will be removed by the VM when the
            # VM successfully comes into existence.
            self.temporary = True
            # Give it a temporary name. Something unique. This is the number
            # of microseconds since the epoch; I figure that it'll work out
            # alright.
            self.template_name = str(int(time.time() * (10 ** 6)))
