#!/usr/local/bin/python
#!/usr/bin/python

import migrator_safe as S
import sys, os

#        - name: DATABASE_LOGLEVEL
#        - name: DATABASE_MIGRATIONS
#        - name: DATABASE_MIGRATOR_INIT
#        - name: DATABASE_MIGRATOR
#        - name: DATABASE_TYPE
#        - name: DATABASE_HOST
#        - name: DATABASE_PORT
#        - name: DATABASE_NAME
#        - name: DATABASE_USER
#        - name: DATABASE_SSLMODE
#        - name: DATABASE_PASSWORD
#        - name: DATABASE_VERSION
#        - name: DATABASE_VERSION_NAME

db = S.connect(
  type =       os.environ['DATABASE_TYPE'],
  host =       os.environ['DATABASE_HOST'],
  port =       os.environ['DATABASE_PORT'],
  database =   os.environ['DATABASE_NAME'],
  user =       os.environ['DATABASE_USER'],
  password =   os.environ['DATABASE_PASSWORD'],
  sslmode =    os.environ['DATABASE_SSLMODE'],
)

migr_new_dir = os.environ['DATABASE_MIGRATIONS']
migr_old_dir = os.environ['DATABASE_MIGRATIONS_OLD']

is_ver = db.is_version_table()
is_files = db.is_files_table()
is_log = db.is_log_table()
ver = db.get_migration_version()
print("bound_version=%s bound_files=%s bound_logs=%s" % (is_ver, is_files, is_log) )

if len(sys.argv)<=1:
  print("Command missing: pre, post, pre-force, post-force, log, get-log")
  sys.exit(1)

elif sys.argv[1]=='pre':
  if not is_ver: # empty table
     print( "empty database" )
  elif not is_files: # legacy mode!
     print( "legacy version=%s" % (ver) )
     S.put_migration_version( migr_old_dir, ver )
  else: # advanced mode
     print( "advanced version=%s" % (ver) )
     #
     files = S.get_migrations( migr_new_dir )
     sfiles = db.get_migrations()
     S.put_migrations( migr_old_dir, sfiles )
     S.put_migration_version( migr_old_dir, ver )
     ver2 = S.compare_migration_tree(files, sfiles)
     if ver2 is not None:
       ver2id = ver2['id']
       print( "down version=%s" % (ver2id) )
       S.put_migration_version( migr_old_dir, ver2id, '.version2' )

elif sys.argv[1]=='pre-force':
  if not is_ver: # empty table
     print( "empty database" )
  elif not is_files: # legacy mode!
     print( "legacy version=%s" % (ver) )
     S.put_migration_version( migr_old_dir, ver )
  else: # advanced mode
     print( "advanced version=%s" % (ver) )
     #
     files = S.get_migrations( migr_new_dir )
     sfiles = db.get_migrations()
     S.put_migrations( migr_old_dir, sfiles )
     S.put_migration_version( migr_old_dir, ver )
     ver2 = S.compare_migration_tree_force(files, sfiles)
     if ver2 is not None:
       ver2id = ver2['id']
       print( "rollback version=%s" % (ver2id) )
       S.put_migration_version( migr_old_dir, ver2id, '.version2' )

elif sys.argv[1]=='post' or sys.argv[1]=='post-force':
  if not is_ver: # empty table
     S.error( "empty database" )
  elif not is_files: # still legacy mode!
     files = S.get_migrations( migr_new_dir )
     db.create_migrations()
     db.put_migrations( files )
  else: # advanced mode
     files = S.get_migrations( os.environ['DATABASE_MIGRATIONS'] )
     db.put_migrations( files, True )

elif sys.argv[1]=='log':
  if not is_log:
     db.create_log()
  db.put_log( sys.stdin.read() )

elif sys.argv[1]=='get-log':
  if not is_log:
     S.warning( "No log" )
  else:
     for v in db.get_log():
       sys.stdout.write("%s\t%d\t%s\n" % (v[0].strftime("%Y-%m-%d %H:%M:%S"), v[1], v[2]))

db.close()
