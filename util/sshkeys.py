#!/usr/bin/env python
# coding: utf-8

import sys
from optparse import OptionParser
import urllib2
import json


class ArgumentException(BaseException):
    pass

class BadMimetype(BaseException):
    pass


class Application:
    def __init__(self, hostname, key, cluster_slug, vm_name, url="%s/cluster/%s/%s/keys/%s/"):
        self.hostname = hostname
        self.key = key
        self.cluster_slug = cluster_slug
        self.vm_name = vm_name
        self.url = url

    def get(self):
        """
        Gets the page specified in __init__
        """
        url = self.url % (self.hostname, self.cluster_slug, self.vm_name, self.key)
        content = urllib2.urlopen(url)
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
        s = "### VM: %s %s\n" % (self.cluster_slug, self.vm_name)
        u = ""
        for i in data:
            # check which user is that
            # if some new, then append the comment line with explanation
            if i[1] != u:
                u = i[1]
                s += "# user %s\n" % u

            # append key
            s += "%s\n" % i[0]
        return s

    def run(self):
        """
        Combines get, parse and printout methods.
        """
        try:
            s = self.printout(self.parse(self.get()))
        except BaseException, e:
            sys.stderr.write("Errors occured, could not retrieve informations.\n")
            sys.stderr.write(str(e))
        else:
            sys.stdout.write(s)


def main():
    parser = OptionParser()
    parser.add_option("-H", "--host", dest="hostname",
            help="Host where Ganeti WebMgr is running")

    parser.add_option("-k", "--key", dest="key",
            help="Ganeti API key used to connect to the application")

    parser.add_option("-c", "--cluster", dest="cluster_slug",
            help="Cluster name")

    parser.add_option("-m", "--machine", dest="vm_name",
            help="Virtual Machine instance name")

    options, args = parser.parse_args(sys.argv)

    # test if every required arg has been passed to argv
    for arg in ["hostname", "key", "cluster_slug", "vm_name"]:
        if not arg in options.__dict__.keys():
            raise ArgumentException("%s option is required" % arg)

    return options


if __name__ == "__main__":
    try:
        options = main()
    except ArgumentException, e:
        print str(e)
        sys.exit(1)
    else:
        a = Application(**options.__dict__)
        a.run()

