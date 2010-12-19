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
    def __init__(self, hostname, api_key, cluster_slug, vm_name, url="http://%s/cluster/%s/%s/keys/%s/"):
        self.hostname = hostname
        self.key = api_key
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
        s = ""
        for i in data:
            # append comment with username
            s += "# added automatically for ganeti web manager user: " + i[1]
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
            sys.stderr.write(str(e)+"\n")
        else:
            sys.stdout.write(s)


def main():
    # TODO: rewrite it
    if len(sys.argv)!=5:
        raise ArgumentException("Too much or too few arguments!")

    options = dict(hostname=sys.argv[1], cluster_slug=sys.argv[2], vm_name=sys.argv[3], api_key=sys.argv[4])

    return options


if __name__ == "__main__":
    try:
        options = main()
    except ArgumentException, e:
        sys.stderr.write(str(e)+"\n"*2)
        sys.stderr.write(
"""Usage:   sshkeys.py  HOSTNAME  CLUSTER_SLUG  VM_NAME  API_KEY

HOSTNAME\thost Ganeti is running on
CLUSTER_SLUG\tcluster short name
VM_NAME\t\tvirtual machine instance name
API_KEY\t\tGaneti API key used to connect to the application
""")
        sys.exit(1)
    else:
        a = Application(**options)
        a.run()

