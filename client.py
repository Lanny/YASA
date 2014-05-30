#!/usr/bin/env python
import socket
import os
import sys
import time
import subprocess

import parse

class YASAClientSession(object):
    def __init__(self, s, db_conn=None):
        self._socket = s
        self._responses = parse.recv_load(self._socket)

        if db_conn:
            self._conn = db_conn
        else:
            self._conn = sqlite3.connect('yasaclient.db')
            self._conn.row_factory = utils.dict_factory

    def _send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self._socket.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent

    def add_to_itunes(self, path):
        """
        Takes a path to a file and adds it to the iTunes library in whatever
        manner is appropriate for the system. Does NOT delete the file after.
        Returns the new path of the file.
        """
        if sys.platform == 'darwin':
            command = """
                      set f to POSIX file "%s"
                      tell application "iTunes"
                          launch
                          try
                              set t to add (f)
                              set loc to location of t
                              set output to POSIX path of loc
                              do shell script "echo " & quoted form of output
                          end try
                      end tell
                      """

            new_path = subprocess.check_output(["osascript", "-e", 
                                                command % path])

            return new_path

        elif sys.platform == 'win32':
            pass
        else:
            raise Exception('Unsupported system, aborting.')

    def communicate(self, message):
        """
        Takes a structure and sends it to the connected server, then waits for
        the server to send a response and returns the parsed response.
        """
        request = parse.dumps(message)
        self._send(request)
        response = next(self._responses)

        return response

    def pull_remote(file_id):
        """
        Grabs a file from the remote host and writes its contents to a 
        temporary file. Returns temp file path and file hash (from remote).
        """
        request = parse.dumps({'ACTION': 'PULL-FILE',
                               'ID': file_id})
        self._send(request)
        file_name = os.tmpnam()
        fd = open(file_name, 'wb')

        buf = ''
        while '\n' not in buf:
            buf += self._socket.recv(1024).decode('utf-8')

        flen, buf = buf.split('\n', 1)
        flen = int(flen.strip())
        totes = len(buf)
        fd.write(buf)

        while totes < flen:
            buf = socket.recv(min(1024, flen-totes))
            totes += len(buf)
            fd.write(buf)

        totes = 0
        buf = ''
        while len(buf) < 16:
            buf += socket.recv(16-len(buf))

        fd.close()

        return fime_name, buf

    def do_pull(self):
        since = (utils.read_settings(self._conn, 'last_update')
                      .get('last_update', 0))
        to_recv = parse.listify(self.communicate({'ACTION': 'PULL',
                                                  'SINCE': since}))

        for x in to_recv:
            from_serv = parse.loads(x)
            if from_serv['type'] == 'new':
                file_path, file_hash = self.pull_remote(from_serv['id'])

                fd = open(file_path, 'rb')
                our_hash = utils.hash_file(fd)
                if our_hash.digest() != file_hash:
                    raise Exception('MD5 digests did not match! Transmission '
                                    'error suspected.')

                it_path = self.add_to_itunes(file_path)
                os.remove(file_path)

                record = utils.generate_file_info(it_path)
                record['server_id'] = from_serv['id']
                utils.insert_file_record(record, self._conn)

    def do_push(self):
        pass

    def sync(self):
        self.do_pull()
        self.do_push()
