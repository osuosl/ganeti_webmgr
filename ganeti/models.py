import os
import sys
import urllib
import urllib2

from django.db import models
from django.contrib.auth.models import User, Group
from simplejson import JSONEncoder, JSONDecoder
from time import sleep
from ganeti_webmgr.util import client
from ganeti_webmgr.util.portforwarder import forward_port
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from datetime import datetime

dec = JSONDecoder()

#HOSTNAME = 'ganeti-test.osuosl.org.bak'
curl = client.GenericCurlConfig()

class MethodRequest(urllib2.Request):
    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


class InstanceManager(object):
    def all(self):
        results = []
        for cluster in Cluster.objects.all():
            results.extend([ Instance(cluster, info['name'], info)
                             for info in cluster.get_cluster_instances_detail() ])
        return results

    def filter(self, **kwargs):
        if 'cluster' in kwargs:
            if isinstance(kwargs['cluster'], Cluster):
                cluster = kwargs['cluster']
            else:
                try:
                    cluster = Cluster.object.get(slug=kwargs['cluster'])
                except:
                    return []
            results = cluster.get_instances()
            del kwargs['cluster']
        else:
            results = self.all()

        for arg, val in kwargs.items():
            if arg == 'user':
                if not isinstance(val, User):
                    try:
                        val = User.objects.get(username__iexact=val)
                    except:
                        return []
                results = [ result for result in results if val in result.users ]
            elif arg == 'group':
                if not isinstance(val, Group):
                    try:
                        val = Group.objects.get(name__iexact=val)
                    except:
                        return []
                results = [ result for result in results
                            if val in result.groups ]
            elif arg == 'name':
                results = [ result for result in results if result.name == val ]
            else:
                results = [ result for result in results
                            if '%s:%s' % (arg, val) in result.tags ]

        return results

    def get(self, **kwargs):
        results = self.filter(**kwargs)
        if len(results) == 1:
            return results[0]
        elif len(results) > 1:
            raise MultipleObjectsReturned("Multiple instances found")
        else:
            raise ObjectDoesNotExist("Could not find an instance")


class Instance(object):
    objects = InstanceManager()

    def __init__(self, cluster, name, info=None):
        self._cluster = cluster
        self.name = name
        self.users = []
        self.groups = []
        self._update(info)

    def _update(self, info=None):
        if not info:
            info = self._cluster.get_instance_info(self.name)

        for attr in info:
            self.__dict__[attr] = info[attr]

        for tag in self.tags:
            if tag.startswith('group:'):
                try:
                    self.groups.append(Group.objects.get(name__iexact=tag.replace('group:','')))
                except:
                    pass
            elif tag.startswith('user:'):
                try:
                    self.users.append(User.objects.get(username__iexact=tag.replace('user:','')))
                except:
                    pass

        if getattr(self, 'ctime', None):
            self.ctime = datetime.fromtimestamp(self.ctime)
        if getattr(self, 'mtime', None):
            self.mtime = datetime.fromtimestamp(self.mtime)

    def set_params(self, **kwargs):
        params = urllib.urlencode(kwargs)
        self._cluster._get_resource('/2/instances/' + self.name + '/modify?' +
                                    params, method='PUT')

    def __repr__(self):
        return "<Instance: '%s'>" % self.name

    def __unicode__(self):
        return self.name


class Cluster(models.Model):
    hostname = models.CharField(max_length=128)
    slug = models.SlugField(max_length=50)
    port = models.PositiveIntegerField(default=5080)
    description = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self.rapi = client.GanetiRapiClient(self.hostname, 
                                              curl_config_fn=curl)
        if self.id:
            self._update()

    def __unicode__(self):
        return self.hostname

    # Update the database records after querying the rapi
    def _update(self):
        self._info = self.rapi.GetInfo()
        for attr in self._info:
            self.__dict__[attr] = self._info[attr]

    def _get_resource(self, resource, method='GET', data=None):
        # Strip trailing slashes, as ganeti-rapi doesn't like them
        resource = resource.rstrip('/')

        # create a password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of ``None``.
        top_level_url = 'https://%s:%d/2/' % (self.hostname, self.port)
        password_mgr.add_password(None, top_level_url,
                                  self.username, self.password)

        handler = urllib2.HTTPBasicAuthHandler(password_mgr)

        # create "opener" (OpenerDirector instance)
        opener = urllib2.build_opener(handler)

        # Install the opener.
        # Now all calls to urllib2.urlopen use our opener.
        urllib2.install_opener(opener)

        req = MethodRequest(method, 'https://%s:%d%s' %
                            (self.hostname, self.port, resource),
                            data=data)
        response = urllib2.urlopen(req)
        if response.code != 200:
            raise ValueError("'%s' is not a valid resource" % resource)
        try:
            contenttype = response.info()['Content-Type']
        except:
            contenttype = None

        if contenttype != 'application/json':
            raise ValueError("Invalid response type '%s'" % contenttype)

        return dec.decode(response.read())

    def get_instance(self, name):
        for inst in self.get_instances():
            if inst.name == name:
                return inst
        return None

    def get_instances(self):
        return [ Instance(self, info['name'], info) for info in self.get_cluster_instances_detail() ]

    def get_cluster_info(self):
        info = self.rapi.GetInfo()
        print info['ctime']
        if 'ctime' in info and info['ctime']:
            info['ctime'] = datetime.fromtimestamp(info['ctime'])
        if 'mtime' in info and info['mtime']:
            info['mtime'] = datetime.fromtimestamp(info['mtime'])
        return info

    def get_cluster_nodes(self):
        return self.rapi.GetNodes()

    def get_cluster_instances(self):
        return self.rapi.GetInstances(False)

    def get_cluster_instances_detail(self):
        return self.rapi.GetInstances(True)

    def get_node_info(self, node):
        return self.rapi.GetNode(node)

    def get_instance_info(self, instance):
        return self.rapi.GetInstanceInfo(instance.strip())

    def set_random_vnc_password(self, instance):
        jobid = self._get_resource('/2/instances/%s/randomvncpass' %
                                   instance.strip(),
                                   method="POST")
        tries = 0
        jobinfo = {}
        while tries < 10:
            jobinfo = self._get_resource('/2/jobs/%s' % jobid)
            if jobinfo['status'] == "error":
                return None
            elif jobinfo['status'] == "success":
                break
            tries += 1
            sleep(0.5)
        if jobinfo:
            return jobinfo['opresult'][0]
        else:
            return None

    def setup_vnc_forwarding(self, instance):
        password = self.set_random_vnc_password(instance)
        info = self.get_instance_info(instance)

        port = info['network_port']
        node = info['pnode']

        os.system("portforwarder.py %d %s:%d" % (port, node, port))
        return (port, password)

    def shutdown_instance(self, instance):
        return self.rapi.ShutdownInstance(instance.strip())

    def startup_instance(self, instance):
        return self.rapi.StartupInstance(instance.strip())

    def reboot_instance(self, instance):
        return self.rapi.RebootInstance(instance.strip())
