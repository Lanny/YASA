#!/usr/bin/env python
import socket
import os

import parse

class YASAServerSession(object):
    def __init__(self, s):
        self._socket = s
        self._session = {}
        self._extensions = []
        self._middleware = []
        self._action_handlers = {
            'HELO': self.helo_command,
            'DEFAULT': self.default_command
        }

    def run(self):
        commands = parse.recv_load(self._socket)

        for command in commands:
            resp = self._handle_command(command)

            # Hook for generators
            if callable(resp):
                pass
            else:
                self._socket.send(resp + '\n')

    def _handle_command(self, command):
        if isinstance(command, parse.ParseError):
            return parse.dumps({'ACTION': 'ERROR',
                                'REASON': 'Command is malformed'})

        in_sess = self._session.copy()

        try:
            resp, sess = self.delegate(command, in_sess)
        except parse.ParsedKeyError, e:
            resp = {'ACTION': 'ERROR',
                    'REASON': 'Missing key: `%s`' % e.missing_key}

        if callable(resp):
            return resp
        else:
            return parse.dumps(resp)

    def delegate(self, command, session):
        """
        Routes a command to the appropriate handler method and returns a
        response, session tuple. There is no promise the session argument will
        not be mutated, but the returned session is always to be prefered.
        """
        responder = self._action_handlers.get(command['ACTION'],
                                              self._action_handlers['DEFAULT'])

        return responder(command, session)

    def helo_command(self, command, session):
        response = {'ACTION': 'OLEH'}
        return response, session

    def default_command(self, command, session):
        response = {'ACTION': 'ERROR',
                    'REASON': 'Unknown action: `%s`' % command['ACTION']}
        return response, session

def serve_forever(port=7454):
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
    serve_forever()
