#!/usr/bin/env python
import socket
import os

import parse

class YASAServerSession(object):
    def __init__(self, s):
        self._socket = s
        self._extensions = []
        self._action_handlers = {
            'HELO': self.helo
        }

    def run(self):
        commands = parse.recv_load(self._socket)

        for command in commands:
            print 'Received %s command' % command['ACTION']

    def delegate(self, line):
        command = parse.loads(line)

    def helo(self):
        pass

def serve_forever(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    s.listen(1)

    while 1:
        conn, addr = s.accept()
        sess = YASAServerSession(conn)
        sess.run()

    conn.close()
        

if __name__ == '__main__':
    serve_forever(7454)
