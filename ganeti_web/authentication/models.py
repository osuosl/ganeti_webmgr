from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from utils.fields import SumIf


class ClusterUser(models.Model):
    """
    Base class for objects that may interact with a Cluster or VirtualMachine.
    """

    name = models.CharField(max_length=128)
    real_type = models.ForeignKey(ContentType, related_name="+",
                                  editable=False, null=True, blank=True)

    def __repr__(self):
        return "<%s: %s>" % (str(self.real_type), self.name)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(ClusterUser, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.cast().get_absolute_url()

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        return self.cast().permissable

    @classmethod
    def _get_real_type(cls):
        return ContentType.objects.get_for_model(cls)

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    def used_resources(self, cluster=None, only_running=True):
        """
        Return dictionary of total resources used by VMs that this ClusterUser
        has perms to.
        @param cluster  if set, get only VMs from specified cluster
        @param only_running  if set, get only running VMs
        """
        # XXX - order_by must be cleared or it breaks annotation grouping since
        #       the default order_by field is also added to the group_by clause
        base = self.virtual_machines.all().order_by()

        # XXX - use a custom aggregate for ram and vcpu count when filtering by
        # running.  this allows us to execute a single query.
        #
        # XXX - quotes must be used in this order.  postgresql quirk
        if only_running:
            sum_ram = SumIf('ram', condition="status='running'")
            sum_vcpus = SumIf('virtual_cpus', condition="status='running'")
        else:
            sum_ram = Sum('ram')
            sum_vcpus = Sum('virtual_cpus')

        base = base.exclude(ram=-1, disk_size=-1, virtual_cpus=-1)

        if cluster:
            base = base.filter(cluster=cluster)
            result = base.aggregate(ram=sum_ram, disk=Sum('disk_size'),
                                    virtual_cpus=sum_vcpus)

            # repack with zeros instead of Nones
            if result['disk'] is None:
                result['disk'] = 0
            if result['ram'] is None:
                result['ram'] = 0
            if result['virtual_cpus'] is None:
                result['virtual_cpus'] = 0
            return result

        else:
            base = base.values('cluster').annotate(uram=sum_ram,
                                                   udisk=Sum('disk_size'),
                                                   uvirtual_cpus=sum_vcpus)

            # repack as dictionary
            result = {}
            for used in base:
                # repack with zeros instead of Nones, change index names
                used["ram"] = used.pop("uram") or 0
                used["disk"] = used.pop("udisk") or 0
                used["virtual_cpus"] = used.pop("uvirtual_cpus") or 0
                result[used.pop('cluster')] = used

            return result


class Profile(ClusterUser):
    """
    Profile associated with a django.contrib.auth.User object.
    """
    user = models.OneToOneField(User)

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def grant(self, perm, obj):
        self.user.grant(perm, obj)

    def set_perms(self, perms, obj):
        self.user.set_perms(perms, obj)

    def get_objects_any_perms(self, *args, **kwargs):
        return self.user.get_objects_any_perms(*args, **kwargs)

    def has_perm(self, *args, **kwargs):
        return self.user.has_perm(*args, **kwargs)

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        return self.user


class Organization(ClusterUser):
    """
    An organization is used for grouping Users.

    Organizations are matched with an instance of contrib.auth.models.Group.
    This model exists so that contrib.auth.models.Group have a 1:1 relation
    with a ClusterUser on which quotas and permissions can be assigned.
    """

    group = models.OneToOneField(Group, related_name='organization')

    def get_absolute_url(self):
        return self.group.get_absolute_url()

    def grant(self, perm, object):
        self.group.grant(perm, object)

    def set_perms(self, perms, object):
        self.group.set_perms(perms, object)

    def get_objects_any_perms(self, *args, **kwargs):
        return self.group.get_objects_any_perms(*args, **kwargs)

    def has_perm(self, *args, **kwargs):
        return self.group.has_perm(*args, **kwargs)

    @property
    def permissable(self):
        """ returns an object that can be granted permissions """
        return self.group
