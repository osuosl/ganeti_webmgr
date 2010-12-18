#!/usr/bin/env python
# coding: utf-8


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-h", "--host", dest="hostname",
            help="Host where Ganeti WebMgr is running")

    parser.add_option("-k", "--key", dest="key",
            help="Ganeti API key used to connect to the application")

    parser.add_option("-c", "--cluster", dest="cluster_slug",
            help="Cluster name")

    parser.add_option("-m", "--machine", dest="vm_name",
            help="Virtual Machine instance name")
