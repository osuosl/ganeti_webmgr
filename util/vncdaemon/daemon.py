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

import SocketServer
import threading
import subprocess
import sys
from optparse import OptionParser, OptionValueError

from server import WebProxyServer
from websocketproxy import WebsocketProxy


class DaemonThread(threading.Thread):
    def __init__(self, pool, host, port, pool_port):
        self.pool = pool
        self.host = host
        self.port = port
        self.pool_port = pool_port
        self.proxy = None
        self.proxy_connected = False
        self.timer = None
        super(DaemonThread, self).__init__()

    def run(self):
        print "new thread run proxy at %s" % self.pool_port
        self.proxy = WebsocketProxy("", self.pool_port, self.host, self.port)
        self.proxy.start_server()

        # append the port
        self.pool.append(self.pool_port)
        print "returned proxy port %s" % self.pool_port


class Daemon:
    def __init__(self, start_port=1000, end_port=2000):
        self.start_port = start_port
        self.end_port = end_port
        self.pool = list( range(self.start_port, self.end_port+1) ) # future compability

    def webproxy(self, host, port, pool_port=None):
        # XXX: check if port isn't taken by someone else
        # XXX: check for any ports in pool (len != 0)
        if not pool_port:
            pool_port = self.pool.pop(0)
        else:
            # XXX: look out for exceptions
            self.pool.pop( self.pool.index(pool_port) )

        # create thread with host, port, pool_port
        t1 = DaemonThread(self.pool, host, port, pool_port)
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
    
    return options


if __name__=="__main__":
    try:
        options = main()

    except OptionValueError, e:
        print "ERROR: %s" % str(e)
        sys.exit(1)

    else:
        d = Daemon(options.begin_port, options.end_port)

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

