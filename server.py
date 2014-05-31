#!/usr/bin/env python
import socket
import os
import sqlite3

import parse
import utils

class YASAServerSession(object):
    def __init__(self, s):
        self._socket = s
        self._session = {}
        self._extensions = []
        self._middleware = []
        self._conn = utils.get_server_connection('server.db')
        self._action_handlers = {
            'HELO': self.helo_command,
            'PULL': self.pull_command,
            'DEFAULT': self.default_command
        }

    def _send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self._socket.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent

    def run(self):
        commands = parse.recv_load(self._socket)

        for command in commands:
            resp = self._handle_command(command)

            # Hook for generators
            if callable(resp):
                pass
            else:
                self._send(resp + '\n')

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

    def pull_command(self, command, session):
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM files WHERE received>?', 
                       [int(command['SINCE'])])
        new_files = cursor.fetchall()
        cursor.execute('SELECT * FROM deleted WHERE del_time>?', 
                       [int(command['SINCE'])])
        del_files = cursor.fetchall()

        l = []
        for record in new_files:
            l.append({'ID': record['id'],
                      'TYPE': 'NEW'})
        for record in del_files:
            l.append({'ID': record['file_id'],
                      'TYPE': 'DELETE'})

        resp = {'ACTION': 'LLUP', 'CHANGES': l}
        return resp, session

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
