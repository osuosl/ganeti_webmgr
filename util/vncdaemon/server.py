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

import re
import SimpleHTTPServer

class WebProxyServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    webproxy_func = None

    settings_url = re.compile(r'^/settings/(?P<act>(begin_port|end_port))/(?P<val>\d*)/?$', re.U)
    request_url = re.compile(r'^/proxy/(?P<host>[^/:]+):(?P<port>\d+)/(?P<pool_port>\d*)', re.U)

    def send_head(self, status=200, ctype="text/html"):
        if status==404:
            self.send_error(404, "File not found")
        else:
            self.send_response(status)
            self.send_header("Content-type", ctype)
        self.end_headers()

    def do_GET(self):
        if self.settings_url.match(self.path):
            # TODO: parse settings page - is it really needed?
            self.send_head(200)
            self.wfile.write("<h1>it worked</h1>")
        
        elif self.request_url.match(self.path):
            r = self.request_url.findall(self.path)
            self.send_head(200)
            self.wfile.write(self.webproxy_func(*r[0]))

        else:
            self.send_head(404)

