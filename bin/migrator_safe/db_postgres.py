
common = None

import sys, base64

import pg8000

def bind(glob):
  global common
  common = glob

class Database(object):
  #
  def __init__(self, host, port, database, user, password, sslmode):
    self.connection = pg8000.connect(
      user=user,
      host=host,
      port=int(port),
      database=database,
      password=password,
#      ssl=dict(cert_reqs=sslmode)
    )
  #
  def close(self):
    self.connection.close()
  #
  def sql_list(self, sql, *args):
    try:
      with self.connection.cursor() as cursor:
        cursor.execute(sql, args)
        rv = []
        for r in cursor:
          rv.append(r)
        return rv
    except pg8000.core.ProgrammingError as e:
      self.connection.rollback()
      sys.stderr.write("ERROR: %s\n" % str(e))
      return None
  #
  def sql_one(self, sql, *args):
    try:
      with self.connection.cursor() as cursor:
        cursor.execute(sql, args)
        row = cursor.fetchone()
        if row is None:
          return None
        return row
    except pg8000.core.ProgrammingError as e:
      self.connection.rollback()
      sys.stderr.write("ERROR: %s\n" % str(e))
      return None
  #
  def sql_exec(self, sql, *args):
    try:
      with self.connection.cursor() as cursor:
        cursor.execute(sql, args)
      return True
    except pg8000.core.ProgrammingError as e:
      #print(repr(sql), repr(args))
      self.connection.rollback()
      sys.stderr.write("ERROR: %s\n" % str(e))
      return False
  #
  def sql_exec_multi(self, sql, rows):
    try:
      with self.connection.cursor() as cursor:
        cursor.executemany(sql, list(rows))
      return True
    except pg8000.core.ProgrammingError as e:
      #print(repr(sql), repr(args))
      self.connection.rollback()
      sys.stderr.write("ERROR: %s\n" % str(e))
      return False
  #
  def sql_is_table(self, name):
    val = self.sql_one("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='%s')" % name)
    if val is None:
      return None
    return val[0]
  #
  #
  def get_migration_version(self):
    val = self.sql_one("SELECT version, dirty FROM %s" % common.TABLE_NAME_VERSION)
    if val is None:
      return None
    return val[0]
  #
  # -- is table exists
  #
  def is_version_table(self):
    return self.sql_is_table(common.TABLE_NAME_VERSION)
  #
  def is_files_table(self):
    return self.sql_is_table(common.TABLE_NAME_FILES)
  #
  def is_log_table(self):
    return self.sql_is_table(common.TABLE_NAME_LOG)
  #
  # -- migrations
  #
  def create_migrations(self):
    rv = self.sql_exec("""
      CREATE TABLE %s (
        name VARCHAR(256) NOT NULL PRIMARY KEY, 
        data_base64 VARCHAR(65536) NOT NULL
      )
    """ % common.TABLE_NAME_FILES)
    if not rv:
      common.error("Can't create migrations table")
    self.connection.commit()
  #
  def get_migrations(self):
    vals = self.sql_list("SELECT name, data_base64 FROM %s" % common.TABLE_NAME_FILES)
    if vals is None:
      return None
    rv = []
    for v in vals:
      try:
        dat=base64.b64decode(v[1])
      except Exception as ee:
        common.error("Can't decode %s base64 from \"%s\"" % (v[0], v[1]))
        continue
      rv.append( common.migration_info(v[0], dat.decode('UTF-8')) )
    return rv
  #
  def put_migrations(self, files, dupmode=False):
    rv = self.sql_exec("DELETE FROM %s" % common.TABLE_NAME_FILES)
    if not rv:
      common.error("Can't cleanup migrations files table")
    if False:
      for f in files:
        rv = self.sql_exec("INSERT INTO %s(name, data_base64) VALUES(%%s, %%s)" % common.TABLE_NAME_FILES, f['name'], f['data.base64'].decode('ascii') )
        if not rv:
          common.error("Can't insert into migrations files table %s" % f['name'])
    else:
      sv = []
      for f in files:
#        sv.append(f['name'])
#        sv.append(f['data.base64'])
        sv.append([ f['name'], f['data.base64'].decode('ascii') ])
      rv = self.sql_exec_multi("INSERT INTO %s(name, data_base64) VALUES (%%s, %%s)" % common.TABLE_NAME_FILES, sv)
      if not rv:
        common.error("Can't insert into migrations files table")
    self.connection.commit()
  #
  # -- log
  #
  def create_log(self):
    rv = self.sql_exec("""
      CREATE TABLE %s (
        ts TIMESTAMP NOT NULL,
        lineno INT NOT NULL,
        message VARCHAR(4090600) NOT NULL,
        PRIMARY KEY(ts, lineno)
      )
    """ % common.TABLE_NAME_LOG)
    if not rv:
      common.error("Can't create log table")
    self.connection.commit()
  #
  def get_log(self):
    vals = self.sql_list("SELECT ts, lineno, message FROM %s" % common.TABLE_NAME_LOG)
    if vals is None:
      return None
    rv = []
    for v in vals:
      rv.append( (v[0], v[1], v[2]) )
    return rv
  #
  def put_log(self, message, ts=None):
    vals = []
    if ts is None:
      for i,l in enumerate(message.splitlines()):
        vals.append([i+1, l ])
      rv = self.sql_exec_multi("INSERT INTO %s(ts, lineno, message) VALUES(NOW(), %%s, %%s)" % common.TABLE_NAME_LOG, vals)
    else:
      for i,l in enumerate(message.splitlines()):
        vals.append([ts,  i+1, l ])
      rv = self.sql_exec_multi("INSERT INTO %s(ts, lineno, message) VALUES(%%s, %%s, %%s)" % common.TABLE_NAME_LOG, vals)
    if not rv:
      common.warning("Can't insert into log table")
    else:
      self.connection.commit()

