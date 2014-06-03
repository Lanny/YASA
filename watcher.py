#!/usr/bin/env python
import os
import hashlib
import time
import sqlite3
import logging

import utils

logging.basicConfig(level=logging.INFO)

def scan(path, conn):
    """
    Walks a directory and compares it to the databse pointed at by `conn`,
    returning a three tuple of files added to or removed from the directory 
    verses its representation in the db respectively. Modified files will be
    included in both added and removed lists. Will update the `last_scan` 
    fields within the db. Note that no effort is made to identify files which 
    have moved.
    """
    cursor = conn.cursor()
    scan_start = time.time()
    added = []
    removed = []

    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            cursor.execute('SELECT * FROM files WHERE path = ? LIMIT 1',
                           [file_path])

            record = cursor.fetchone()

            if not record:
                added.append(file_path)
            else:
                fs_mtime = os.path.getmtime(file_path)

                if fs_mtime > record['mtime']:
                    # This file is marked as having been modified since we
                    # last saw it, time to hash to check for changes.
                    fd = open(file_path, 'rb')
                    hash_value = utils.hash_file(fd).hexdigest()

                    if hash_value != record['hash']:
                        added.append(file_path)
                        removed.append(record['id'])

                cursor.execute('UPDATE files SET last_scan=? WHERE id=?',
                               [scan_start, record['id']])

    conn.commit()

    cursor.execute('SELECT * FROM files WHERE last_scan < ?', [scan_start])
    removed.extend(cursor.fetchall())
    cursor.close()

    return added, removed

def reconcile(path, conn):
    """
    Given a path and a connection to a DB, alter the DB to reflect the present
    structure of the directory.
    """
    cursor = conn.cursor()
    added, removed = scan(path, conn)

    for path in added:
        logging.info("Adding file: %s" % path)
        utils.arrow(path,
                    (utils.generate_file_info),
                    (utils.insert_file_record, conn))

    for record in removed:
        logging.info("Recording as gone: %s" % path)
        cursor.execute(('INSERT INTO deleted (del_time, server_id, path) '
                        'VALUES (?, ?, ?)'),
                       [time.time(), record['server_id'], record['path']])
        cursor.execute('DELETE FROM files WHERE id=?', [record['id']])

    conn.commit()
    cursor.close()

if __name__ == '__main__':
    conn = utils.get_client_connection('yasaclient.db')
    lib_dir = utils.read_settings(conn, 'lib_dir').get('lib_dir')

    reconcile(lib_dir, conn)
