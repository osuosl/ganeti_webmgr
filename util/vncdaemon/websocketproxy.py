# coding: UTF-8

import sys
import socket
import ssl
from base64 import b64encode, b64decode

# Python 2.4 support
try: from hashlib import md5
except: from md5 import md5

import struct
from select import select
import traceback


class WebsocketError(socket.error):
    pass

class WebsocketClose(WebsocketError):
    pass


class WebsocketProxy:
    DEBUG = False
    flash_policy_response = """<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>\n"""
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

    def __init__(self, listen_host, listen_port, target_host, target_port,
                ssl_only=False, certfile=None, keyfile=None, buffer_size=65536):
        # listening settings
        self.listen_host = listen_host
        self.listen_port = int(listen_port)

        # target VNC server settings
        self.target_host = target_host
        self.target_port = int(target_port)

        # SSL settings
        self.ssl_only = ssl_only  # allow only encrypted connections
        self.certfile = certfile  # certificate file
        self.keyfile = keyfile    # certificate file
        
        # buffering
        self.buffer_size = buffer_size

    def log(self, message):
        """
        Simple logging function.
        """
        if self.DEBUG:
            sys.stdout.write("%s\n" % message)
            sys.stdout.flush()

    def encode(self, buf):
        """
        Encode bytes in base64.
        """
        buf = b64encode(buf)
        return "\x00%s\xff" % buf

    def decode(self, buf):
        """
        Decode bytes from base64.
        """
        if buf.count("\xff") > 1:
            return [b64decode(d[1:]) for d in buf.split('\xff')]
        else:
            return [b64decode(buf[1:-1])]

    def generate_md5(self, keys):
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

    def parse_handshake(self, handshake):
        """
        Utility for parsing the received handshake.
        """
        ret = {}
        req_lines = handshake.split("\r\n")
        if not req_lines[0].startswith("GET "):
            raise WebsocketError("Invalid handshake: no GET request line")

        ret["path"] = req_lines[0].split(" ")[1]
        for line in req_lines[1:]:
            if not line:
                break

            var, val = line.split(": ")
            ret[var] = val

        if req_lines[-2] == "":
            ret["key3"] = req_lines[-1]

        return ret

    def do_handshake(self, sock):
        """
        Shake hands.
        """
        # peek, but don't read the data
        handshake = sock.recv(1024, socket.MSG_PEEK)

        if not handshake:
            self.log("ERROR: got empty handshake")
            sock.close()
            return False

        elif handshake.startswith("<policy-file-request/>"):
            handshake = sock.recv(1024)
            self.log("Handshake: got flash policy")
            sock.send(self.flash_policy_response)
            sock.close()
            return "flash"
        
        elif handshake[0] in ("\x16", "\x80"):
            retsock = ssl.wrap_socket(
                sock,
                server_side = True,
                certfile = self.certfile,
                keyfile = self.keyfile,
            )
            scheme = "wss"
            self.log("Handshake: using SSL/TLS socket")

        elif self.ssl_only:
            self.log("Handshake: non-SSL connections forbidden")
            sock.close()
            return False

        else:
            retsock = sock
            scheme = "ws"
            self.log("Handshake: using non-SSL socket")

        handshake = retsock.recv(4096)
        if len(handshake) == 0:
            raise WebsocketClose("Handshake: client closed connection")

        h = self.parse_handshake(handshake)

        if h.get("key3"):
            trailer = self.generate_md5(h)
            pre = "Sec-"
            self.log("Handshake: using protocol version 76")

        else:
            trailer = ""
            pre = ""
            self.log("Handshake: using protocol version 75")

        response = "\r\n".join(self.server_response) % (pre, h["Origin"], pre,
                    scheme, h["Host"], h["path"], pre, trailer)

        retsock.send(response)
        return retsock

    # TODO: clean this up, maybe base on proxy2()?
    def proxy(self, client, target):
        """
        Proxy between browser (web socket) and VNC server.
        """
        cqueue = []
        cpartial = ""
        tqueue = []
        rlist = [client, target]

        while True:
            wlist = []

            if tqueue: wlist.append(target)
            if cqueue: wlist.append(client)

            ins, outs, excepts = select(rlist, wlist, [], 30)
            if excepts:
                raise WebsocketError("Socket exception")

            if target in outs:
                dat = tqueue.pop(0)
                sent = target.send(dat)
                if sent != len(dat):
                    tqueue.insert(0, dat[sent:])

            if client in outs:
                dat = cqueue.pop(0)
                sent = client.send(dat)
                if sent != len(dat):
                    cqueue.insert(0, dat[sent:])

            if target in ins:
                buf = target.recv(self.buffer_size)
                if len(buf) == 0:
                    raise WebsocketClose("Target closed")
                cqueue.append(self.encode(buf))

            if client in ins:
                buf = client.recv(self.buffer_size)
                if len(buf) == 0:
                    raise WebsocketClose("Client closed")

                if buf == "\xff\x00":
                    raise WebsocketClose("Client sent orderly close frame")
                
                elif buf[-1] == "\xff":
                    if cpartial:
                        tqueue.extend(self.decode(cpartial+buf))
                        cpartial = ""
                    else:
                        tqueue.extend(self.decode(buf))

                else:
                    cpartial = cpartial + buf

    def proxy2(self, source, dest):
        """
        Proxy between browser (web socket) and VNC server.
        Doesn't work as expected.
        Taken from vncauthproxy.
        """
        while True:
            d = source.recv(8096)
            if d == '':
                self.log("Server or client closed connection")
                break
            dest.sendall(d)
        source.close()
        dest.close()

    def handle(self, client):
        """
        Bridge-function between proxy and server.
        """
        log = "VNC proxy: %s"
        self.log(log % "connecting to %s:%s" % (self.target_host, self.target_port))

        tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tsock.connect( (self.target_host, self.target_port) )

        try:
            self.proxy(client, tsock)
        except BaseException, e:
            if tsock:
                tsock.close()
            raise e

    def start_server(self, connections=1):
        """
        Starts server.

        @param connections  max number of active connections
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind( (self.listen_host, self.listen_port) )
        self.socket.listen(connections)

        self.log("Waiting for connections on %s:%s" % (self.listen_host,
                 self.listen_port))

        connection = None
        try:
            # when using browser without Websockets, so that it uses Flash object
            # for creating sockets, Flash establishes two connections, one by one
            # we don't want to create two separate threads for flash, so we use
            # this loop to handle upcoming Flash connections
            for i in range(2):
                self.socket.settimeout(30.0)  # timeout set to 30s
                connection, address = self.socket.accept()
                self.socket.settimeout(None)  # timeout disabled
                # TODO: suggestion: timeout 30s everywhere?

                self.log("Client connection from %s:%s" % address)

                # make handshake
                csock = self.do_handshake(connection)

                if isinstance(csock, str)  and  csock=="flash":
                    # flash
                    self.log("Waiting for next Flash connection")
                    continue  # second iteration

                elif not csock:
                    raise WebsocketError("No connection after handshake")

                self.handle(csock)
                break # we don't need second iteration

        except BaseException, e:
            self.log("ERROR: %s" % str(e))
            self.log(traceback.format_exc())

        finally:
            self.socket.close()
            if connection and connection!=self.socket:
                connection.close()


if __name__ == "__main__":
    proxy = WebsocketProxy("localhost", 8888, "localhost", 5901)
    proxy.start_server()
