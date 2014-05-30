#!/usr/bin/env python
import os
import time
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