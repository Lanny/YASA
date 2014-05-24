#!/usr/bin/env python
import os
import time
import hashlib

def hash_file(fd):
    h = hashlib.md5()
    block = fd.read(h.block_size)

    while block:
        h.update(block)
        block = fd.read(h.block_size)

    return h

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
            'mtime': int(os.path.getmtime(path)),
            'last_internal_update': t,
            'last_scan': t }
