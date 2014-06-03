#!/usr/bin/env python
import os
import sys
import time
import sqlite3
import hashlib
import socket
import urllib
import uuid

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def arrow(exp, *args):
    """
    A sad approximation of clojure's arrow macro.
    """
    for arg in args:
        if isinstance(arg, tuple):
            exp = arg[0](*((exp,) + arg[1:]))
        else:
            exp = arg(exp)

    return exp

def get_client_connection(path):
    """
    Returns a sqlite3 db connection to the provided path. Creates and inits 
    the db if none exists.
    """
    must_init = not os.path.exists(path)

    conn = sqlite3.connect(path)
    conn.row_factory = dict_factory

    if must_init:
        cursor = conn.cursor()
        schema = open('clientschema.sql', 'r')
        cursor.executescript(schema.read())
        schema.close()

        if sys.platform == 'darwin':
            lib_dir = os.path.join(os.path.expanduser('~'),
                                   'Music/iTunes/iTunes Media/Music')
        elif sys.platform == 'win32':
            # TODO: support windows
            raise Exception('Unsupported system, aborting.')
        else:
            raise Exception('Unsupported system, aborting.')

        write_settings(conn, lib_dir=lib_dir)

    return conn

def get_server_connection(path):
    """
    Returns a sqlite3 db connection to the provided path. Creates and inits 
    the db if none exists.
    """
    must_init = not os.path.exists(path)

    conn = sqlite3.connect(path)
    conn.row_factory = dict_factory

    if must_init:
        cursor = conn.cursor()
        schema = open('serverschema.sql', 'r')
        cursor.executescript(schema.read())
        schema.close()

        storage_dir = os.path.join(os.path.expanduser('~'), 'yasastorage')
        try:
            os.makedirs(storage_dir)
        except OSError:
            pass # Directory probably already exists

        write_settings(conn, storage_dir=storage_dir)
        conn.commit()

    return conn

def _send(socket, msg):
    totes_sent = 0
    while totes_sent < len(msg):
        sent = socket.send(msg[totes_sent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totes_sent += sent

def push_file(path, socket, hash_code=None, buf_size=1024):
    """
    Given a path to a file and optionally a hash, sends both over the socket
    per the YASA convention. Will generate hash if none is provided.
    """
    print 'Pushin'
    if not hash_code:
        fd = open(path, 'rb')
        hash_code = hash_file(fd).digest()
        fd.close()

    fd = open(path, 'rb')
    fsize = os.fstat(fd.fileno()).st_size
    _send(socket, '%d\n' % fsize)

    totes = 0
    while totes < fsize:
        send_size = min(buf_size, fsize-totes)
        _send(socket, fd.read(send_size))
        totes += send_size

    _send(socket, hash_code)

def pull_file(path, socket, buf_size=1024):
    """
    Given a path to a writable file and a socket, receive YASA transmitted 
    data over the socket and write it to a new file at `path`. Returns the
    hash of the file _according to the sender_.
    """
    print 'Pullin'
    fd = open(path, 'wb')

    buf = ''
    while '\n' not in buf:
        buf += socket.recv(10).decode('utf-8')

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

    return buf

def hash_file(fd, hash_fn=hashlib.md5):
    """
    Takes a file descriptor, returns a hash object of that file's contents.
    """
    h = hash_fn()
    block = fd.read(h.block_size)

    while block:
        h.update(block)
        block = fd.read(h.block_size)

    return h

def insert_file_record(record, conn):
    """
    Inserts a file record, represented as a python dictionary, into the 
    database pointed to by the connection. Returns new record id.
    """
    cursor = conn.cursor()

    field_names = ['path', 'hash', 'mtime', 'server_id',
                   'last_internal_update', 'last_scan']
    sql = 'INSERT INTO files (%s) VALUES (%s)' % (
        ', '.join(field_names), ', '.join(['?' for x in field_names]))

    cursor.execute(sql, [record[f] for f in field_names])

    return cursor.lastrowid

def generate_file_info(path):
    """
    Returns a dictionary representing a db record representing the file at
    the specified path.
    """
    f = open(path, 'rb')
    h = hash_file(f)
    f.close()
    t = int(time.time())

    # This is bad, we should do this at system boundries. It's on the todo
    if not isinstance(path, unicode):
        path = path.decode('UTF-8')

    return {'path': path,
            'hash': h.hexdigest(),
            'server_id': None,
            'mtime': int(os.path.getmtime(path)),
            'last_internal_update': t,
            'last_scan': t }

def read_settings(conn, *settings):
    """
    Returns records from the settings table with with specified keys. Returns
    a dictionary. Requested values that do not appear in the table will not be
    present in the return value.
    """
    cur = conn.cursor()
    cur.execute('SELECT * FROM settings WHERE key IN (%s)' % 
                ', '.join(['?' for x in settings]), settings)

    rv = {}
    for record in cur.fetchall():
        rv[record['key']] = record['value']

    return rv

def write_settings(conn, **settings):
    """
    Writes kwarg/value pairs to the settings table. If a key already exists 
    it will be replaced silently.
    """
    cur = conn.cursor()
    for k, v in settings.items():
        cur.execute('INSERT INTO settings (key, value) VALUES (?, ?)', [k, v])

    conn.commit()

def get_or_guess_node_ref(conn):
    """
    Retreives this node's node refrence. If none exists in the database, try
    to guess it and write that guess back to the db. Returns a uuid, addr,
    volitility tuple of types string, string, boolean respectively.
    """
    rv = read_settings(conn, 'my-uuid', 'my-addr', 'my-vol')

    if len(rv) != 3:
        req = urllib.urlopen('http://icanhazip.com/')
        rv['my-addr'] = req.read().strip()
        req.close()

        rv['my-uuid'] = '%s@%s' % (socket.gethostname(), unicode(uuid.uuid4()))
        rv['my-vol'] = True

        write_settings(conn, **rv)

    return rv['my-uuid'], rv['my-addr'], rv['my-vol']
