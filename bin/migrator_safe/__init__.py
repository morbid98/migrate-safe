
import glob, base64, sys, os, re
import os.path as path
import hashlib

# --------------------------------------------------------------------------------------------------------------------------------

TABLE_NAME_VERSION = 'schema_migrations'
TABLE_NAME_FILES = 'schema_migrations_files'
TABLE_NAME_LOG = 'schema_migrations_log'

RE_MIGRATION_FILENAME = re.compile('([0-9]+)_(\w+)\.(up|down)\.sql')

# --------------------------------------------------------------------------------------------------------------------------------

def error(msg, *iargs):
  raise Exception("ERROR: %s" % (msg % iargs))

def warning(msg, *iargs):
  sys.stderr.write("%s\n" % ("WARNING: %s" % (msg % iargs)) )

def map_by_keys(srcmap, keys):
  return dict((k, srcmap[k]) for k in keys)

def array_by_map_keys(srcmap, keys):
  return list(srcmap[k] for k in keys)

# --------------------------------------------------------------------------------------------------------------------------------

def connect(type, **args):
  if type=='postgres':
    import migrator_safe.db_postgres as db
    db.bind( __import__(__name__) )
  else:
    raise Exception("Database type %s is not supported" % type)
  #
  return db.Database(**args)

# --------------------------------------------------------------------------------------------------------------------------------

def migration_info(name, data):
  keys = migration_keys(name)
  return {
    'name': name,
    'id': keys[0],
    'info': keys[1],
    'dir': keys[2],
    'data': data,
    'data.base64': base64.b64encode(data.encode('UTF-8')),
    'data.sha': hashlib.sha1(data.encode('UTF-8')).hexdigest()
  }

# --------------------------------------------------------------------------------------------------------------------------------

def get_migrations(dirname):
  rv = []
  mask = "%s/*.sql" % dirname
  #sys.stderr.write("%s\n" % mask)
  for fn in sorted(glob.glob(mask)):
    with open(fn) as f:
      rv.append( migration_info( path.basename(fn), f.read() ) )
  return rv

def put_migrations(dirname, migs):
  for m in migs:
    fn = "%s/%s" % (dirname, m['name'])
    with open(fn, 'w') as f:
      f.write(m['data'])

def put_migration_version(dirname, version, name='.version'):
  fn = "%s/%s" % (dirname, name)
  with open(fn, 'w') as f:
    f.write(str(version))


def migration_keys(name):
  m = re.search(RE_MIGRATION_FILENAME, name)
  if m is None:
    error("Invalid migration filename \"%s\"" % name)
  return m.group(1), m.group(2), m.group(3)

def migration_map(migs, dir='up'):
  rv = {}
  for m in migs:
    if m['dir']!=dir:
      continue # skip
    if m['id'] in rv:
      error("Duplicate of migration %s" % m['name'])
    rv[m['id']] = m
  return rv

# --------------------------------------------------------------------------------------------------------------------------------

def migration_map_diff_keys(ms1, ms2):
  k1 = sorted(ms1.keys())
  k2 = sorted(ms2.keys())
  same = min(len(k1), len(k2))
  for i in range(0, same):
    if k1[i]!=k2[i]:
      same = i
      break
  return k1[:same], k1[same:], k2[same:]

def migration_compare_validate(m1, m2, strict=True):
  if m1['id']!=m2['id']:
    if strict:
      error("Migration id mismatch \"%s\" and \"%s\"" % (m1['name'], m2['name']))
    return False
  if m1['dir']!=m2['dir']:
    if strict:
      error("Migration dir mismatch \"%s\" and \"%s\"" % (m1['name'], m2['name']))
    return False
  if m1['info']!=m2['info']:
    if strict:
      error("Migration info mismatch \"%s\" and \"%s\"" % (m1['name'], m2['name']))
    return False
  if m1['data']!=m2['data']:
    if strict:
      error("Migration data mismatch \"%s\" and \"%s\" sha %s and %s" % (m1['name'], m2['name'], m1['data.sha'], m2['data.sha']))
    return False
  return True

def migration_array_compare_validate(am1, am2, strict=True):
  if len(am1)!=len(am2):
    error("Migration list array not the same length %d!=%d" % (len(am1), len(am2)))
  for i in range(0, len(am1)):
    v1 = am1[i]
    v2 = am2[i]
    rv = migration_compare_validate(v1, v2)
    if not rv:
      return False
  return True

def compare_migration_map(ms1, ms2, strict=True):
  ks, kd, ka = migration_map_diff_keys(ms1, ms2)
  if len(ka)>0 and len(kd)>0 and strict:
    error("Migration list branching at #%d, %s!=%s len %d and %d\n - %s\n - %s" % (len(ks), ka[0], kd[0], len(ka), len(kd), ka[0], kd[0]))
  s1 = array_by_map_keys(ms1, ks)
  s2 = array_by_map_keys(ms2, ks)
  migration_array_compare_validate(s1, s2, True) # this means damaged list
  return s1, array_by_map_keys(ms1, kd), array_by_map_keys(ms2, ka)

def compare_migration_tree(migs1, migs2):
  m1u = migration_map(migs1, 'up')
  m1d = migration_map(migs1, 'down')
  m2u = migration_map(migs2, 'up')
  m2d = migration_map(migs2, 'down')
  #
  res1 = compare_migration_map(m1u, m2u, True)
  res2 = compare_migration_map(m1d, m2d, True)
  #
  if len(res2[0]):
    return res2[0][-1]

def compare_migration_tree_force(migs1, migs2):
  m1u = migration_map(migs1, 'up')
  m1d = migration_map(migs1, 'down')
  m2u = migration_map(migs2, 'up')
  m2d = migration_map(migs2, 'down')
  #
  res1 = compare_migration_map(m1u, m2u, False)
  res2 = compare_migration_map(m1d, m2d, False)
  #
  if len(res2[0]):
    return res2[0][-1]

# --------------------------------------------------------------------------------------------------------------------------------
