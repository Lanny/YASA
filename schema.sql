CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  path TEXT,
  hash TEXT,
  mtime INTEGER,
  last_internal_update INTEGER,
  last_scan INTEGER,
  UNIQUE(path));

-- Contains records that have been deleted from the library and must be
-- propogated
CREATE TABLE deleted (
  id INTEGER PRIMARY KEY,
  del_time INTEGER,
  path TEXT );

CREATE TABLE node_refs (
  id INTEGER PRIMARY KEY,
  uuid TEXT,
  address TEXT,
  stability INTEGER,
  last_asked INTEGER,
  last_told INTEGER,
  UNIQUE(uuid),
  UNIQUE(address) ON CONFLICT REPLACE);



CREATE TABLE settings (
  key TEXT,
  value TEXT, 
  UNIQUE(key) ON CONFLICT REPLACE);
