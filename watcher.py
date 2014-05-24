#!/usr/bin/env python
import os
import hashlib
import time
import sqlite3

def scan(path, cursor):
    """
    Walks a directory and compares it to the databse pointed at by `cursor`,
    returning a three tuple of files added to or removed from the directory 
    verses its representation in the db respectively. Modified files will be
    included in both added and removed lists. Will update the `last_scan` 
    fields within the db. Note that no effort is made to identify files which 
    have moved.
    """
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

                if fs_mtime > record.mtime:
                    # This file is marked as having been modified since we
                    # last saw it, time to hash to check for changes.
                    pass

                cursor.execute('UPDATE files SET (last_scan) ? WHERE id = ?',
                               [scan_start, record.id])

    cursor.commit()

    cursor.execute('SELECT id FROM files WHERE last_scan < ?', [scan_start])
    removed = [x.id for x in cursor.fetchall()]

    return added, removed

if __name__ == '__main__':
    must_init = not os.path.exists('node.db')

    conn = sqlite3.connect('node.db')
    cursor = conn.cursor()

    if must_init:
        schema = open('schema.sql', 'r')
        cursor.executescript(schema.read())
        schema.close()

    added, removed = scan('testlib_one', cursor)
    for p in added: print p
    print ''
    for r in removed: print r


