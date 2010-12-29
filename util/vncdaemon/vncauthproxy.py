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


import os
import sys

# Python 2.4 support
try: from hashlib import md5
except: from md5 import md5

from base64 import b64encode, b64decode
import struct
import logging
import gevent

import rfb

from gevent import socket, ssl, Timeout
from gevent.select import select

# TODO: WebSocket
# - HARD include Flash support? Maybe need to change something in VncAuthProxy._run
class WebSocketError(socket.error):
    pass

class WebSocket:
    server_response = [
        "HTTP/1.1 101 Web Socket Protocol Handshake",
        "Upgrade: WebSocket",
        "Connection: Upgrade",
        "%sWebSocket-Origin: %s",
        "%sWebSocket-Location: %s://%s%s",
        "%sWebSocket-Protocol: sample",
        "",
        "%s",
    ]
    
    
    def __init__(self, socket, log=None, ssl_only=False, certfile=None, keyfile=None):
        self.socket = socket
        self.log = log # logging function
        self.ssl_only = ssl_only
        self.certfile, self.keyfile = certfile, keyfile

        self._ws_handshake()
    

    def _generate_md5(self, keys):
        """
        Generate MD5 hash needed in SSL socket transmission.
        """
        key1 = keys["Sec-WebSocket-Key1"]
        key2 = keys["Sec-WebSocket-Key2"]
        key3 = keys["key3"]
        spaces1 = key1.count(" ")
        spaces2 = key2.count(" ")
        num1 = int("".join([c for c in key1 if c.isdigit()])) / spaces1
        num2 = int("".join([c for c in key2 if c.isdigit()])) / spaces2

        return md5(struct.pack(">II8s", num1, num2, key3)).digest()
    

    def _parse_ws_handshake(self, handshake):
        """
        Parse WebSocket handshake into more friendly form
        """
        ret = {}
        req_lines = handshake.split("\r\n")

        if not req_lines[0].startswith("GET "):
            raise WebsocketError("WS Handshake: invalid, no GET request line")

        ret["path"] = req_lines[0].split(" ")[1]

        for line in req_lines[1:]:
            if not line: break
            
            var, val = line.split(": ")
            ret[var] = val

        if req_lines[-2] == "":
            ret["key3"] = req_lines[-1]

        return ret


    def _ws_handshake(self):
        """
        Perform WebSocket handshake
        """
        # peek, but don't read the data
        handshake = self.socket.recv(1024, socket.MSG_PEEK)

        if not handshake:
            self.client.close()
            raise WebSocketError("WS: Got empty handshake")

        # TODO: flash in here?
        elif handshake[0] in ("\x16", "\x80"):
            retsock = ssl.SSLSocket(
                self.socket,
                server_side = True,
                certfile = self.certfile,
                keyfile = self.keyfile,
            )
            scheme = "wss"
            self.log("WS Handshake: using SSL/TLS socket")

        elif self.ssl_only:
            self.socket.close()
            raise WebSocketError("WS Handshake: non-SSL connections forbidden")

        else:
            retsock = self.socket
            scheme = "ws"
            self.log("WS Handshake: using non-SSL socket")

        handshake = retsock.recv(4096)
        if len(handshake) == 0:
            retsock.close()
            raise WebSocketError("Handshake: client closed connection")

        h = self._parse_ws_handshake(handshake)

        if h.get("key3"):
            trailer = self._generate_md5(h)
            pre = "Sec-"
            self.log("WS Handshake: using protocol version 76")

        else:
            trailer = ""
            pre = ""
            self.log("WS Handshake: using protocol version 75")

        response = "\r\n".join(self.server_response) % (pre, h["Origin"], pre,
                    scheme, h["Host"], h["path"], pre, trailer)

        retsock.send(response)
        self.socket = retsock
        return True

    
    def encode(self, buf):
        """
        Encode bytes in base64.
        """
        buf = b64encode(buf)
        return "\x00%s\xFF" % buf
    

    def decode(self, buf):
        """
        Decode bytes from base64.
        """
        if buf.count("\xff") > 1:
            return "".join([b64decode(d[1:]) for d in buf.split('\xff')])
        else:
            return b64decode(buf[1:-1])
    

    def recv(self, *args, **kwargs):
        data = self.socket.recv(*args, **kwargs)
        data = self.decode(data)
        return data
    

    def send(self, data, *args, **kwargs):
        data = self.encode(data)
        return self.socket.send(data, *args, **kwargs)
    

    def sendall(self, data, *args, **kwargs):
        data = self.encode(data)
        return self.socket.sendall(data, *args, **kwargs)
    

    def close(self):
        return self.socket.close()

    def fileno(self):
        return self.socket.fileno()


class VncAuthProxy(gevent.Greenlet):
    """
    Simple class implementing a VNC Forwarder with MITM authentication as a
    Greenlet

    VncAuthProxy forwards VNC traffic from a specified port of the local host
    to a specified remote host:port. Furthermore, it implements VNC
    Authentication, intercepting the client/server handshake and asking the
    client for authentication even if the backend requires none.

    It is primarily intended for use in virtualization environments, as a VNC
    ``switch''.

    """
    id = 1

    def __init__(self, sport, daddr, dport, password, connect_timeout=30,
            websocket_support=False, ssl_only=False, cerfile=None, keyfile=None,
            pool=[]):
        """
        @type sport: int
        @param sport: source port
        @type daddr: str
        @param daddr: destination address (IPv4, IPv6 or hostname)
        @type dport: int
        @param dport: destination port
        @type password: str
        @param password: password to request from the client
        @type connect_timeout: int
        @param connect_timeout: how long to wait for client connections
                                (seconds)

        """
        gevent.Greenlet.__init__(self)
        self.id = VncAuthProxy.id
        VncAuthProxy.id += 1
        self.sport = sport
        self.daddr = daddr
        self.dport = dport
        self.password = password
        self.log = logging
        self.server = None
        self.client = None
        self.timeout = connect_timeout

        self.websocket_support = websocket_support
        
        self.ssl_only = ssl_only
        self.certfile, self.keyfile = cerfile, keyfile

        self.pool = pool

        self.buffer_size = 65536

    def _cleanup(self):
        """Close all active sockets and exit gracefully"""
        if self.server:
            self.server.close()
        if self.client:
            self.client.close()

        # push the server port back in the pool
        self.pool.append(self.sport)

        raise gevent.GreenletExit

    def info(self, msg):
        logging.info("[C%d] %s" % (self.id, msg))

    def debug(self, msg):
        logging.debug("[C%d] %s" % (self.id, msg))

    def warn(self, msg):
        logging.warn("[C%d] %s" % (self.id, msg))

    def error(self, msg):
        logging.error("[C%d] %s" % (self.id, msg))

    def critical(self, msg):
        logging.critical("[C%d] %s" % (self.id, msg))

    def __str__(self):
        return "VncAuthProxy: %d -> %s:%d" % (self.sport, self.daddr, self.dport)

    def _forward(self, source, dest, use_timeout=False):
        """
        Forward traffic from source to dest

        @type source: socket
        @param source: source socket
        @type dest: socket
        @param dest: destination socket

        """
        timeout = None
        if use_timeout:
            timeout = Timeout(5)

        try:
            while True:
                # XXX: gevent issue: not working at all
                # hack is Timeout object
                socket.wait_readwrite(source.fileno(), timeout=self.timeout)

                d = source.recv(self.buffer_size)
                if not d:
                    # start timeout
                    if use_timeout  and  not timeout.pending:
                        timeout.start()
                        self.info("Started new timeout")
                        if source==self.client: self.info("in client")

                else:
                    # restart timeout
                    if use_timeout  and  timeout.pending:
                        timeout.cancel()
                        timeout.start()
                        #self.info("Restarted timeout")

                    dest.sendall(d)

                    if d=="\xff\x00":
                        self.info("Client sent closing frame")
                        break

        except BaseException:
            self.info("Timeout exception")
            if source==self.client: self.info("in client")

        finally:
            self._cleanup()

    def _handshake(self):
        """
        Perform handshake/authentication with a connecting client

        Outline:
        1. Client connects
        2. We fake RFB 3.8 protocol and require VNC authentication
        3. Client accepts authentication method
        4. We send an authentication challenge
        5. Client sends the authentication response
        6. We check the authentication
        7. We initiate a connection with the backend server and perform basic
           RFB 3.8 handshake with it.
        8. If the above is successful, "bridge" both connections through two
           "fowrarder" greenlets.

        """
        
        if self.websocket_support:
            # WebSocket class performs handshake, SSL initialization and other
            # clever things. It "wraps" gevent.socket class.
            try:
                self.client = WebSocket(self.client, self.info, self.ssl_only,
                    self.certfile, self.keyfile)

            except WebSocketError, e:
                self.critical(str("e"))
                self._cleanup()

        self.client.send(rfb.RFB_VERSION_3_8 + "\n")
        client_version = self.client.recv(1024)
        if not rfb.check_version(client_version):
            self.error("Invalid version: %s" % client_version)
            self._cleanup()
        self.debug("Requesting authentication")
        auth_request = rfb.make_auth_request(rfb.RFB_AUTHTYPE_VNC)
        self.client.send(auth_request)
        res = self.client.recv(1024)
        type = rfb.parse_client_authtype(res)
        if type == rfb.RFB_AUTHTYPE_ERROR:
            self.warn("Client refused authentication: %s" % res[1:])
        else:
            self.debug("Client requested authtype %x" % type)

        if type != rfb.RFB_AUTHTYPE_VNC:
            self.error("Wrong auth type: %d" % type)
            self.client.send(rfb.to_u32(rfb.RFB_AUTH_ERROR))
            self._cleanup()

        # Generate the challenge
        challenge = os.urandom(16)
        self.client.send(challenge)
        response = self.client.recv(1024)
        if len(response) != 16:
            self.error("Wrong response length %d, should be 16" % len(response))
            self._cleanup()

        if rfb.check_password(challenge, response, password):
            self.debug("Authentication successful!")
        else:
            self.warn("Authentication failed")
            self.client.send(rfb.to_u32(rfb.RFB_AUTH_ERROR))
            self._cleanup()

        # Accept the authentication
        self.client.send(rfb.to_u32(rfb.RFB_AUTH_SUCCESS))

        # Try to connect to the server
        tries = 50

        while tries:
            tries -= 1

            # Initiate server connection
            for res in socket.getaddrinfo(self.daddr, self.dport, socket.AF_UNSPEC,
                                          socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
                af, socktype, proto, canonname, sa = res
                try:
                    # TODO: encrypt this?
                    # only if possible
                    self.server = socket.socket(af, socktype, proto)
                except socket.error, msg:
                    self.server = None
                    continue

                try:
                    self.debug("Connecting to %s:%s" % sa[:2])
                    self.server.connect( (sa[0], int(sa[1])) )
                    self.debug("Connection to %s:%s successful" % sa[:2])
                except socket.error, msg:
                    self.server.close()
                    self.server = None
                    continue

                # We succesfully connected to the server
                tries = 0
                break

            # Wait and retry
            gevent.sleep(0.2)

        if self.server is None:
            self.error("Failed to connect to server")
            self._cleanup()

        version = self.server.recv(1024)
        if not rfb.check_version(version):
            self.error("Unsupported RFB version: %s" % version.strip())
            self._cleanup()

        self.server.send(rfb.RFB_VERSION_3_8 + "\n")

        res = self.server.recv(1024)
        types = rfb.parse_auth_request(res)
        if not types:
            self.error("Error handshaking with the server")
            self._cleanup()

        else:
            self.debug("Supported authentication types: %s" %
                           " ".join([str(x) for x in types]))

        if rfb.RFB_AUTHTYPE_NONE not in types:
            self.error("Error, server demands authentication")
            self._cleanup()

        self.server.send(rfb.to_u8(rfb.RFB_AUTHTYPE_NONE))

        # Check authentication response
        res = self.server.recv(4)
        res = rfb.from_u32(res)

        if res != 0:
            self.error("Authentication error")
            self._cleanup()

        # Bridge client/server connections
        self.workers = [gevent.spawn(self._forward, self.client, self.server, True),
                        gevent.spawn(self._forward, self.server, self.client)]
        gevent.joinall(self.workers)

        del self.workers
        self._cleanup()

    def _run(self):
        sockets = []

        # Use two sockets, one for IPv4, one for IPv6. IPv4-to-IPv6 mapped
        # addresses do not work reliably everywhere (under linux it may have
        # been disabled in /proc/sys/net/ipv6/bind_ipv6_only).
        for res in socket.getaddrinfo(None, self.sport, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                if af == socket.AF_INET6:
                    # Bind v6 only when AF_INET6, otherwise either v4 or v6 bind
                    # will fail.
                    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except socket.error, msg:
                s = None
                continue;

            try:
                s.bind(sa)
                s.listen(1)
                self.debug("Listening on %s:%d" % sa[:2])
            except socket.error, msg:
                self.error("Error binding to %s:%d: %s" %
                               (sa[0], sa[1], msg[1]))
                s.close()
                s = None
                self._cleanup()

            if s:
                sockets.append(s)

        if not sockets:
            self.error("Failed to listen for connections")
            self._cleanup()

        self.log.debug("Waiting for client to connect")
        rlist, _, _ = select(sockets, [], [], timeout=self.timeout)

        if not rlist:
            self.info("Timed out, no connection after %d sec" % self.timeout)
            self._cleanup()

        for sock in rlist:
            self.client, addrinfo = sock.accept()
            self.info("Connection from %s:%d" % addrinfo[:2])
            # TODO: flash connection?

            # Close all listening sockets, we only want a one-shot connection
            # from a single client.
            for listener in sockets:
                listener.close()
            break

        self._handshake()


if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-s", "--socket", dest="ctrl_socket",
                      help="UNIX socket path for control connections",
                      default="/tmp/vncproxy.sock",
                      metavar="PATH")
    parser.add_option("-d", "--debug", action="store_true", dest="debug",
                      help="Enable debugging information")
    parser.add_option("-l", "--log", dest="logfile", default=None,
                      help="Write log to FILE instead of stdout",
                      metavar="FILE")
    parser.add_option("-t", "--connect-timeout", dest="connect_timeout",
                      default=30, type="int", metavar="SECONDS",
                      help="How long to listen for clients to forward")
    parser.add_option("-B", "--begin-port", dest="begin_port", default=7000,
                      help="beginning port for the pool", type="int")
    parser.add_option("-E", "--end-port", dest="end_port", default=8000,
                      help="ending port for the pool", type="int")
    parser.add_option("-w", "--websockets", dest="websockets", action="store_true",
                      help="Enable WebSockets support", default=False)
    parser.add_option("--sslonly", dest="ssl_only", action="store_true",
                      default=False,
                      help="allow only SSL connections")
    parser.add_option("--cert", dest="ssl_cert", default=None,
                      help="SSL certificate file")
    parser.add_option("--key", dest="ssl_key", default=None,
                      help="SSL key file (if separate from cert)")

    (opts, args) = parser.parse_args(sys.argv[1:])

    lvl = logging.DEBUG if opts.debug else logging.INFO

    logging.basicConfig(level=lvl, filename=opts.logfile,
                        format="%(asctime)s %(levelname)s: %(message)s",
                        datefmt="%m/%d/%Y %H:%M:%S")

    if os.path.exists(opts.ctrl_socket):
        logging.critical("Socket '%s' already exists" % opts.ctrl_socket)
        sys.exit(1)

    if not 0 <= opts.begin_port <= 65536:
        logging.critical("Begin pool port should be in range 0..65536")
        sys.exit(1)
    
    if not 0 <= opts.end_port <= 65536:
        logging.critical("End pool port should be in range 0..65536")
        sys.exit(1)

    if not opts.begin_port < opts.end_port:
        logging.critical("Begin pool port should be smaller than end port")
        sys.exit(1)

    if not (opts.end_port - opts.begin_port) > 100:
        logging.critical("Too few ports in pool, try lower begin pool port or higher end pool port")
        sys.exit(1)

    if (opts.ssl_only and not os.path.exists(opts.ssl_cert)) or \
       (opts.ssl_cert and not os.path.exists(opts.ssl_cert)):
        logging.critical("You must specify existing certificate file")
        sys.exit(1)
    elif opts.ssl_cert:
        opts.ssl_cert = os.path.abspath(opts.ssl_cert)

    if opts.ssl_key and not os.path.exists(opts.ssl_key):
        logging.critical("You must specify existing key file")
        sys.exit(1)
    elif opts.ssl_key:
        opts.ssl_file = os.path.abspath(opts.ssl_file)

    if opts.ssl_cert and opts.ssl_cert == opts.ssl_key:
        logging.critical("Certificate and key files must not be the same")
        sys.exit(1)

    # TODO: make this tunable? chgrp as well?
    old_umask = os.umask(0077)

    ctrl = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ctrl.bind(opts.ctrl_socket)

    os.umask(old_umask)

    ctrl.listen(1)
    logging.info("Initalized, waiting for control connections at %s" %
                 opts.ctrl_socket)

    pool = list(range(opts.begin_port, opts.end_port+1))

    while True:
        try:
            client, addr = ctrl.accept()
        except KeyboardInterrupt:
            break

        logging.info("New control connection")
        line = client.recv(1024).strip()
        try:
            # Control message format:
            # TODO: make this json-based?
            # TODO: support multiple forwardings in the same message?
            # <source_port>:<destination_address>:<destination_port>:<password>
            # <password> will be used for MITM authentication of clients
            # connecting to <source_port>, who will subsequently be forwarded
            # to a VNC server at <destination_address>:<destination_port>
            sport, daddr, dport, password = line.split(':')

            if not sport:
                # TODO: check for len()
                sport = pool.pop(0)

            elif int(sport) not in pool:
                raise Exception("Not available")

            else:
                # TODO: look out for exceptions
                sport = pool.pop( pool.index(int(sport)) )

            logging.info("New forwarding [%d -> %s:%d]" %
                         (int(sport), daddr, int(dport)))

            client.send("%d\n" % sport)

        except:
            logging.warn("Malformed request: %s" % line)
            client.send("FAILED\n")
            client.close()
            continue

        else:
            client.close()

        VncAuthProxy.spawn(sport, daddr, dport, password, opts.connect_timeout,
                opts.websockets, opts.ssl_only, opts.ssl_cert, opts.ssl_key,
                pool)

    os.unlink(opts.ctrl_socket)
    sys.exit(0)
