CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  server_id INTEGER,
  path TEXT,
  hash TEXT,
  mtime INTEGER,
  last_internal_update INTEGER,
  last_scan INTEGER,
  UNIQUE(server_id));

-- Contains records that have been deleted from the library and must be
-- propogated
CREATE TABLE deleted (
  id INTEGER PRIMARY KEY,
  server_id INTEGER,
  del_time INTEGER,
  path TEXT );

CREATE TABLE settings (
  key TEXT,
  value TEXT, 
  UNIQUE(key) ON CONFLICT REPLACE);
