import re
from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey


ssh_public_key_re = re.compile(r'^ssh-(rsa|dsa|dss) [A-Z0-9+/=]+ .+$',
                               re.IGNORECASE)
ssh_public_key_error = _("Enter a valid RSA or DSA SSH key.")
validate_sshkey = RegexValidator(ssh_public_key_re, ssh_public_key_error,
                                 "invalid")


class QuerySetManager(models.Manager):
    """
    Useful if you want to define manager methods that need to chain. In this
    case create a QuerySet class within your model and add all of your methods
    directly to the queryset. Example:

    class Foo(models.Model):
        enabled = fields.BooleanField()
        dirty = fields.BooleanField()

        class QuerySet:
            def active(self):
                return self.filter(enabled=True)
            def clean(self):
                return self.filter(dirty=False)

    Foo.objects.active().clean()
    """

    def __getattr__(self, name, *args):
        # Cull under/dunder names to avoid certain kinds of recursion. Django
        # isn't super-bright here.
        if name.startswith('_'):
            raise AttributeError
        return getattr(self.get_query_set(), name, *args)

    def get_query_set(self):
        return self.model.QuerySet(self.model)


class GanetiError(models.Model):
    """
    Class for storing errors which occured in Ganeti
    """
    cluster = models.ForeignKey("clusters.Cluster", related_name="errors")
    msg = models.TextField()
    code = models.PositiveIntegerField(blank=True, null=True)

    # XXX could be fixed with django-model-util's TimeStampedModel
    timestamp = models.DateTimeField()

    # determines if the errors still appears or not
    cleared = models.BooleanField(default=False)

    # cluster object (cluster, VM, Node) affected by the error (if any)
    obj_type = models.ForeignKey(ContentType, related_name="ganeti_errors")
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey("obj_type", "obj_id")

    objects = QuerySetManager()

    class Meta:
        ordering = ("-timestamp", "code", "msg")

    def __unicode__(self):
        base = u"[%s] %s" % (self.timestamp, self.msg)
        return base

    class QuerySet(QuerySet):

        def clear_errors(self, obj=None):
            """
            Clear errors instead of deleting them.
            """

            qs = self.filter(cleared=False)

            if obj:
                qs = qs.get_errors(obj)

            return qs.update(cleared=True)

        def get_errors(self, obj):
            """
            Manager method used for getting QuerySet of all errors depending
            on passed arguments.

            @param  obj   affected object (itself or just QuerySet)
            """
            from ganeti_webmgr.clusters.models import Cluster

            if obj is None:
                raise RuntimeError("Implementation error calling get_errors()"
                                   "with None")

            # Create base query of errors to return.
            #
            # if it's a Cluster or a queryset for Clusters, then we need to
            # get all errors from the Clusters. Do this by filtering on
            # GanetiError.cluster instead of obj_id.
            if isinstance(obj, (Cluster,)):
                return self.filter(cluster=obj)

            elif isinstance(obj, (QuerySet,)):
                if obj.model == Cluster:
                    return self.filter(cluster__in=obj)
                else:
                    ct = ContentType.objects.get_for_model(obj.model)
                    return self.filter(obj_type=ct, obj_id__in=obj)

            else:
                ct = ContentType.objects.get_for_model(obj.__class__)
                return self.filter(obj_type=ct, obj_id=obj.pk)

    def __repr__(self):
        return "<GanetiError '%s'>" % self.msg

    @classmethod
    def store_error(cls, msg, obj, code, **kwargs):
        """
        Create and save an error with the given information.

        @param  msg  error's message
        @param  obj  object (i.e. cluster or vm) affected by the error
        @param code  error's code number
        """
        from ganeti_webmgr.clusters.models import Cluster
        ct = ContentType.objects.get_for_model(obj.__class__)
        is_cluster = isinstance(obj, Cluster)

        # 401 -- bad permissions
        # 401 is cluster-specific error and thus shouldn't appear on any other
        # object.
        if code == 401:
            if not is_cluster:
                # NOTE: what we do here is almost like:
                #  return self.store_error(msg=msg, code=code, obj=obj.cluster)
                # we just omit the recursiveness
                obj = obj.cluster
                ct = ContentType.objects.get_for_model(Cluster)
                is_cluster = True

        # 404 -- object not found
        # 404 can occur on any object, but when it occurs on a cluster, then
        # any of its children must not see the error again
        elif code == 404:
            if not is_cluster:
                # return if the error exists for cluster
                try:
                    c_ct = ContentType.objects.get_for_model(Cluster)
                    return cls.objects.filter(msg=msg, obj_type=c_ct,
                                              code=code,
                                              obj_id=obj.cluster_id,
                                              cleared=False)[0]

                except (cls.DoesNotExist, IndexError):
                    # we want to proceed when the error is not
                    # cluster-specific
                    pass

        # XXX use a try/except instead of get_or_create().  get_or_create()
        # does not allow us to set cluster_id.  This means we'd have to query
        # the cluster object to create the error.  we can't guaranteee the
        # cluster will already be queried so use create() instead which does
        # allow cluster_id
        try:
            return cls.objects.filter(msg=msg, obj_type=ct, obj_id=obj.pk,
                                      code=code, **kwargs)[0]

        except (cls.DoesNotExist, IndexError):
            cluster_id = obj.pk if is_cluster else obj.cluster_id

            return cls.objects.create(timestamp=datetime.now(), msg=msg,
                                      obj_type=ct, obj_id=obj.pk,
                                      cluster_id=cluster_id, code=code,
                                      **kwargs)


class Quota(models.Model):
    """
    A resource limit imposed on a ClusterUser for a given Cluster.  The
    attributes of this model represent maximum values the ClusterUser can
    consume.  The absence of a Quota indicates unlimited usage.
    """
    user = models.ForeignKey("authentication.ClusterUser", related_name='quotas')
    cluster = models.ForeignKey("clusters.Cluster", related_name='quotas')

    ram = models.IntegerField(default=0, null=True, blank=True)
    disk = models.IntegerField(default=0, null=True, blank=True)
    virtual_cpus = models.IntegerField(default=0, null=True, blank=True)


class SSHKey(models.Model):
    """
    Model representing user's SSH public key. Virtual machines rely on
    many ssh keys.
    """
    key = models.TextField(validators=[validate_sshkey])
    #filename = models.CharField(max_length=128) # saves key file's name
    user = models.ForeignKey(User, related_name='ssh_keys')
