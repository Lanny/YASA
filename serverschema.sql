CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  path TEXT,
  hash TEXT,
  received INTEGER,
  UNIQUE(path));

-- Contains records that have been deleted from the library and must be
-- propogated
CREATE TABLE deleted (
  id INTEGER PRIMARY KEY,
  file_id INTEGER,
  del_time INTEGER,
  path TEXT );

CREATE TABLE settings (
  key TEXT,
  value TEXT, 
  UNIQUE(key) ON CONFLICT REPLACE);
