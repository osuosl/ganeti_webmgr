#!/usr/bin/env python
# coding: utf-8

from optparse import OptionParser
from urllib2 import urlopen
from urlparse import urlparse, urlunparse
import sys

from django.utils import simplejson as json

parser = OptionParser()
parser.add_option("-c", "--cluster", help="cluster to retrieve keys from")
parser.add_option("-i", "--instance", help="instance to retrieve keys from")

def main():
    options, arguments = parser.parse_args()
    if len(arguments) < 2:
        parser.error("an API key and hostname are required")
    if options.instance and not options.cluster:
        parser.error("instances cannot be specified without a cluster")

    app = Application(arguments[0], arguments[1],
                      cluster_slug=options.cluster, vm_name=options.instance)
    app.run()

class ArgumentException(Exception):
    """
    There was a bad argument, or something like that.
    """

class BadMimetype(Exception):
    """
    There was a bad MIME type, or something like that.
    """

class Application(object):
    def __init__(self, api_key, hostname, cluster_slug=None, vm_name=None):
        if cluster_slug is not None:
            if vm_name is not None:
                path = "/cluster/%s/%s/keys/%s/" % (cluster_slug, vm_name,
                                                    api_key)
            else:
                path = "/cluster/%s/keys/%s/" % (cluster_slug, api_key)
        else:
            path = "/keys/%s/" % api_key

        split = urlparse(hostname)
        self.url = urlunparse(split._replace(path=path))

    def get(self):
        """
        Gets the page specified in __init__
        """

        content = urlopen(self.url)
        if content.info()["Content-Type"] != "application/json":
            raise BadMimetype("It's not JSON")
        return content.read()

    def parse(self, content):
        """
        Parses returned results from JSON into Python list
        """

        return json.loads(content)

    def printout(self, data):
        """
        Returns string with authorized_keys file syntax and some comments
        """

        s = ["%s added automatically for ganeti web manager user: %s" % i
             for i in data]
        return "\n".join(s)

    def run(self):
        """
        Combines get, parse and printout methods.
        """
        try:
            s = self.printout(self.parse(self.get()))
        except Exception, e:
            sys.stderr.write("Errors occured, could not retrieve informations.\n")
            sys.stderr.write(str(e)+"\n")
        else:
            sys.stdout.write(s)

if __name__ == "__main__":
    main()
