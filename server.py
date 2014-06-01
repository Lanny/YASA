#!/usr/bin/env python
import socket
import os
import sqlite3
import time

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
            'PULL-FILE': self.pull_file_command,
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

            if not resp:
                pass
            elif callable(resp): # Hook for generators
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

        if not resp:
            return None
        elif callable(resp):
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

    def pull_file_command(self, command, session):
        """
        Serves the file with a specified server ID to the client.
        """
        cursor = self._conn.cursor()
        sid = int(command['ID'])
        cursor.execute('SELECT path, hash FROM files WHERE id=?', [sid])
        record = cursor.fetchone()

        utils.push_file(record['path'], self._socket,
                        hash_code=record['hash'].decode('hex'))

        return None, session

    def push_command(self, command, session):
        cursor = self._conn.cursor()

        if command['TYPE'] == 'NEW':
            cursor.execute('INSERT INTO files (received) VALUES (?)', 
                           time.time())
            sid = cursor.lastrowid
            resp = parse.dumps({'ACTION': 'HSUP',
                                'ID': sid,
                                'DONE': 0})
            self._send(resp + '\n')
            file_path = os.path.join( 
                utils.read_settings(self._conn, 'storage_dir')['storage_dir'],
                '%d.mp3' % sid)

            digest = utils.pull_file(file_path, self._socket)
            our_digest = utils.hash_file(open(file_path, 'rb')).digest()

            if our_digest != digest:
                cursor.execute('DELETE FROM files WHERE id=?', [sid])
                resp = {'ACTION': 'ERROR',
                        'REASON': 'Hash mismatch, record revoked, retransmit'}
                self._conn.commit()
                return resp, session

            cursor.execute('UPDATE files SET path=?, hash=? WHERE id=?',
                           [file_path, digest.encode('hex'), sid])
            self._conn.commit()

            resp = {'ACTION': 'HSUP',
                    'DONE': 1}
            return resp, session

        elif command['TYPE'] == 'DELETE':
            sid = int(command['ID'])
            cursor.execute(
                'INSERT INTO deleted (file_id, del_time) VALUES (?, ?)',
                [sid, time.time()])
            cursor.execute('DELETE FROM files WHERE id=?', [sid])

            resp = {'ACTION': 'HSUP',
                    'DONE': 1}
            return resp, session
        else:
            resp = {'ACTION': 'ERROR',
                    'REASON': 'Unknown PUSH type: %s' % command['TYPE']}
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
