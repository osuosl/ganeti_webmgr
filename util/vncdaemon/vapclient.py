#!/usr/bin/env python
#

# Copyright (c) 2010 GRNET SA
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import sys
import socket
import json

CTRL_SOCKET = "/tmp/vncproxy.sock"

def request_forwarding(server, sport, daddr, dport, password):
    try:
        host, port = server
        port = int(port)
        sport = int(sport) if sport else None
        dport = int(dport)
        if not password:
            return False

        request = json.dumps({"sport":sport, "daddr":daddr, "dport":dport, "password":password})

        ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ctrl.connect( (host, port) )
        ctrl.send(request)
        response = ctrl.recv(1024).strip()
        ctrl.close()

        if response.startswith("FAIL"):
            return False
        else:
            return response

    except:
        return False

if __name__ == '__main__':
    print request_forwarding(sys.argv[1].split(":"), *sys.argv[2:])
