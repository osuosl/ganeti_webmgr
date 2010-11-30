#!/usr/bin/env python

# Copyright (C) 2010 Oregon State University et al.
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


import os
import sys
from socket import *
from select import select

ACCEPT_TIMEOUT = 30 # seconds
BUFFER = 2048

def handler(client, remote):
    server = socket(AF_INET, SOCK_STREAM)
    server.connect(remote)
    
    while True:
        rlist, wlist, xlist = select([client, server], [], [server, client])
        if xlist:
            client.close()
            server.close()
            break
        for end in rlist:
            buff = end.recv(BUFFER)
            if len(buff) == 0:
                sys.exit(0)

            if end == server:
                client.send(buff)
            elif end == client:
                server.send(buff)


def forward_port(lport, remote, accept_timeout=ACCEPT_TIMEOUT):
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', lport))
    s.listen(1)
    s.settimeout(accept_timeout)
    try:
        (client, addrinfo) = s.accept()
        s.close()
        handler(client, remote)
    except timeout:
        sys.stderr.write("Timed out\n")
        sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: %s <local_port> <remote_host:remote_port>" % sys.argv[0]
        sys.exit(127)

    try:
        lport = int(sys.argv[1])
    except:
        print "Error, local port must be int"
        sys.exit(1)
    
    if lport <= 0 or lport >= 65536:
        print "Error, invalid port specified: %d" % lport
        sys.exit(1)

    rhost, rport = sys.argv[2].split(':')

    try:
        rport = int(rport)
    except:
        print "Error, remote port must be int"
        sys.exit(1)

    if rport <= 0 or rport >= 65536:
        print "Error, invalid port specified: %d" % lport
        sys.exit(1)

    if os.fork() == 0:
        os.setsid()
        if os.fork() == 0:
            for fd in range(0,10):
                try:
                    os.close(fd)
                except:
                    pass
            i = os.open("/dev/null", os.O_RDONLY)
            i = os.open("/tmp/koko.log", os.O_WRONLY|os.O_CREAT|os.O_APPEND, 0600)
            os.dup2(1,2)
            forward_port(lport, (rhost, rport))
        else:
            os._exit(0)
    else:
        sys.exit(0)
