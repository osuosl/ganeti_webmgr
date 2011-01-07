# coding: utf-8
# Python 2.4 support
try: from hashlib import md5
except: from md5 import md5

import struct
from base64 import b64encode, b64decode
from gevent import socket, ssl


class WebSocketError(socket.error):
    pass
class WebSocketFlash(socket.error):
    pass


class WebSocket:
    policy_response = '<cross-domain-policy><allow-access-from domain="*" ' + \
                      'to-ports="*" /></cross-domain-policy>\n'
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
            raise WebSocketError("WS Handshake: invalid, no GET request line")

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
            self.socket.close()
            raise WebSocketError("WS: Got empty handshake")

        elif handshake.startswith("<policy-file-request/>"):
            handshake = self.socket.recv(1024)
            self.log("Sending flash policy response")
            self.socket.send(self.policy_response)
            self.socket.close()
            raise WebSocketFlash("WS: Got Flash handshake")

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
