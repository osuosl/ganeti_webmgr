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
    def __init__(self, api_key, hostname, cluster_slug=None, vm_name=None):
        if cluster_slug and vm_name:
            self.url = "http://%s/cluster/%s/%s/keys/%s/" % \
                  (hostname, cluster_slug, vm_name, api_key)
        elif cluster_slug:
            self.url = "http://%s/cluster/%s/keys/%s/" % \
                       (hostname, cluster_slug, api_key)
        else:
            self.url = "http://%s/keys/%s/" % (hostname, api_key)

    def get(self):
        """
        Gets the page specified in __init__
        """
        content = urllib2.urlopen(self.url)
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
        s = []
        for i in data:
            # append key and comment with username
            s.append("%s  added automatically for ganeti web manager user: %s\n" % \
                    (i[0], i[1]))
        return "".join(s)

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
    if len(sys.argv)<3:
        raise ArgumentException("Too much or too few arguments!")
    return sys.argv[1:]


if __name__ == "__main__":
    try:
        options = main()
    except ArgumentException, e:
        sys.stderr.write(str(e)+"\n"*2)
        sys.stderr.write(
"""Usage:   sshkeys.py API_KEY  HOSTNAME  [CLUSTER_SLUG  [VM_NAME]]

API_KEY\t\tGaneti API key used to connect to the application
HOSTNAME\thost Ganeti is running on
CLUSTER_SLUG\t(optional) cluster short name, if not given all ssh keys for all clusters are retrieved
VM_NAME\t\t(optional) virtual machine instance name, if not given all ssh keys for the cluster are retrieved
""")
        sys.exit(1)
    else:
        try:
            a = Application(*options)
            a.run()
        except Exception, e:
            sys.stderr.write('error retrieving sshkeys')
            sys.stderr.write(str(e))
