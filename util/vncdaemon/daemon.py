#!/usr/bin/env python2

# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
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

import sys
import os.path
import threading
import SocketServer
from optparse import OptionParser, OptionValueError

from server import WebProxyServer
from websocketproxy import WebsocketProxy


class DaemonThread(threading.Thread):
    def __init__(self, pool, host, port, pool_port, ssl_only, ssl_cert, ssl_key):
        self.pool = pool
        self.host = host
        self.port = port
        self.pool_port = pool_port

        self.ssl_only = ssl_only
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        self.proxy = None
        super(DaemonThread, self).__init__()

    def run(self):
        print "new thread run proxy at %s" % self.pool_port
        self.proxy = WebsocketProxy("", self.pool_port, self.host, self.port,
            self.ssl_only, self.ssl_cert, self.ssl_key)
        self.proxy.start_server()

        # append the port
        self.pool.append(self.pool_port)
        print "returned proxy port %s" % self.pool_port


class Daemon:
    def __init__(self, start_port=1000, end_port=2000,
                 ssl_only=False, ssl_cert=None, ssl_key=None):
        self.start_port = start_port
        self.end_port = end_port
        self.pool = list( range(self.start_port, self.end_port+1) ) # future compability
        self.ssl_only = ssl_only
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

    def webproxy(self, host, port, pool_port=None):
        # XXX: check if port isn't taken by someone else
        # XXX: check for any ports in pool (len != 0)
        if not pool_port:
            pool_port = self.pool.pop(0)
        else:
            # XXX: look out for exceptions
            self.pool.pop( self.pool.index(pool_port) )

        # create thread with host, port, pool_port
        t1 = DaemonThread(self.pool, host, port, pool_port, self.ssl_only,
                self.ssl_cert, self.ssl_key)
        t1.start()

        return "%s" % pool_port


def main():
    parser = OptionParser()
    parser.add_option("-H", "--host", dest="hostname", default="localhost",
            help="server hostname", metavar="HOSTNAME")
    parser.add_option("-p", "--port", dest="port", default=8888,
            help="server port", metavar="PORT", type="int")
    parser.add_option("-B", "--begin-port", dest="begin_port", default=7000,
            help="beginning port for the pool", type="int")
    parser.add_option("-E", "--end-port", dest="end_port", default=8000,
            help="ending port for the pool", type="int")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
            default=False,
            help="verbose mode")
    parser.add_option("--sslonly", dest="ssl_only", action="store_true",
            default=False,
            help="Allow only SSL connections")
    parser.add_option("--cert", dest="ssl_cert", default=None,
            help="SSL certificate file")
    parser.add_option("--key", dest="ssl_key", default=None,
            help="SSL key file (if separate from cert)")
    
    options, args = parser.parse_args()

    if not 0 <= options.port <= 65536:
        raise OptionValueError("Server port should be in range 0..65536")

    if not 0 <= options.begin_port <= 65536:
        raise OptionValueError("Begin pool port should be in range 0..65536")
    
    if not 0 <= options.end_port <= 65536:
        raise OptionValueError("End pool port should be in range 0..65536")

    if not options.begin_port < options.end_port:
        raise OptionValueError("Begin pool port should be smaller than end port")

    if not (options.end_port - options.begin_port) > 100:
        raise OptionValueError("Too few ports in pool, try lower begin pool port or higher end pool port")

    if (options.ssl_only and not os.path.exists(options.ssl_cert)) or \
       (options.ssl_cert and not os.path.exists(options.ssl_cert)):
        raise OptionValueError("You must specify existing certificate file")
    elif options.ssl_cert:
        options.ssl_cert = os.path.abspath(options.ssl_cert)

    if options.ssl_key and not os.path.exists(options.ssl_key):
        raise OptionValueError("You must specify existing key file")
    elif options.ssl_key:
        options.ssl_file = os.path.abspath(options.ssl_file)

    if options.ssl_cert and options.ssl_cert == options.ssl_key:
        raise OptionValueError("Certificate and key files must not be the same")
    
    return options


if __name__=="__main__":
    try:
        options = main()

    except OptionValueError, e:
        print "ERROR: %s" % str(e)
        sys.exit(1)

    else:
        d = Daemon(
            start_port = options.begin_port,
            end_port = options.end_port,
            ssl_only = options.ssl_only,
            ssl_cert = options.ssl_cert,
            ssl_key = options.ssl_key,
        )

        WebsocketProxy.DEBUG = options.verbose
        handler = WebProxyServer
        handler.webproxy_func = d.webproxy

        httpd = None
        try:
            httpd = SocketServer.TCPServer((options.hostname, options.port), handler)

            print "serving at %s:%s" % (options.hostname, options.port)
            httpd.serve_forever()

        except KeyboardInterrupt:
            pass

        except BaseException, e:
            print "ERROR: %s" % str(e)

        finally:
            if httpd and httpd.socket:
                httpd.socket.close()

