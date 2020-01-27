#!/bin/bash

VERSION=0.14

export DATABASE_MIGRATIONS_OLD="${DATABASE_MIGRATIONS_OLD:-/migrations-old}"

export DATABASE_DBTOOL=${DATABASE_DBTOOL:-migrator-dbtool.py}
export DATABASE_FORCE=${DATABASE_FORCE:-false}
export DATABASE_TYPE=${DATABASE_TYPE:-postgres}
export DATABASE_LOGLEVEL=${DATABASE_LOGLEVEL:-debug}

export DATABASE_LOG_FILE="${DATABASE_LOG_FILE:-/var/log/migration.log}"

export DATABASE_OLD_VERSIONFILE="$DATABASE_MIGRATIONS_OLD/.version"
export DATABASE_ROLLBACK_VERSIONFILE="$DATABASE_MIGRATIONS_OLD/.version2"


exec 1> >(tee "$DATABASE_LOG_FILE")
exec 2>&1

# --------------------------------------------------------------------------------------------------------------------------------



function Ex() {
  echo "+$@" >&2
  "$@"
}

function Exe() {
  echo "+$@" >&2
  "$@"
  local ec=$?
  if (( $ec != 0 )) ; then
    echo "  Exit code $ec" >&2
    exit $ec
  fi
}

# --------------------------------------------------------------------------------------------------------------------------------

function dump_vars() {
  echo VERSION=$VERSION
  echo "DATABASE_LOGLEVEL=$DATABASE_LOGLEVEL"
  echo "DATABASE_FORCE=$DATABASE_FORCE"
  echo "DATABASE_VERSION=$DATABASE_VERSION"
  echo "DATABASE_VERSION_NAME=$DATABASE_VERSION_NAME"
  echo "DATABASE_MIGRATIONS=$DATABASE_MIGRATIONS"
  echo "DATABASE_MIGRATIONS_OLD=$DATABASE_MIGRATIONS_OLD"
  echo "DATABASE_MIGRATOR=$DATABASE_MIGRATOR"
  echo "DATABASE_MIGRATOR_INIT=$DATABASE_MIGRATOR_INIT"
  echo "DATABASE_TYPE=$DATABASE_TYPE"
  echo "DATABASE_HOST=$DATABASE_HOST"
  echo "DATABASE_PORT=$DATABASE_PORT"
  echo "DATABASE_NAME=$DATABASE_NAME"
  echo "DATABASE_USER=$DATABASE_USER"
  echo "DATABASE_SSLMODE=$DATABASE_SSLMODE"
  echo "DATABASE_PASSWORD=$DATABASE_PASSWORD"
}

# --------------------------------------------------------------------------------------------------------------------------------

function logFinish() {
  cat "$DATABASE_LOG_FILE" | Ex "$DATABASE_DBTOOL" log
}

function logExe() {
  Ex "$@"
  local ec=$?
  if (( $ec != 0 )) ; then
    echo "  Exit code $ec"
    logFinish
    exit $ec
  fi
}

function exec_migration() {
  if [ -n "$DATABASE_MIGRATOR_INIT" ] ; then
    Exe $DATABASE_MIGRATOR_INIT
  fi
  if [[ $DATABASE_LOGLEVEL == debug ]] ; then
    echo "----------------------- Dump of migrator:"
    Ex ls -l "$DATABASE_MIGRATOR"
    Ex ldd "$DATABASE_MIGRATOR"
    echo "----------------------- End dump of migrator."
    echo "----------------------- Dump of migrations:"
    Ex ls -l "$DATABASE_MIGRATIONS"
    echo "----------------------- End dump of migrations."
  fi
  if [ ! -x "$DATABASE_MIGRATOR" ] ; then
    echo "ERROR: Migrator tool at \"$DATABASE_MIGRATOR\" is not correct" >&2
    exit 4
  fi
  if [ ! -d "$DATABASE_MIGRATIONS" ] ; then
    echo "ERROR: Migrations at \"$DATABASE_MIGRATIONS\" is not correct" >&2
    exit 4
  fi
  if [ ! -d "$DATABASE_MIGRATIONS_OLD" ] ; then
    Exe mkdir "$DATABASE_MIGRATIONS_OLD"
  fi
  
  #
  if [[ $1 == force ]] ; then
    logExe "$DATABASE_DBTOOL" pre-force
  else
    logExe "$DATABASE_DBTOOL" pre
  fi
  #
  if true ; then
    if [[ $DATABASE_LOGLEVEL == debug ]] ; then
      echo "----------------------- Dump of previous migrations:"
      Ex ls -l "$DATABASE_MIGRATIONS"
      echo "----------------------- End dump of previous migrations."
    fi
  fi
  #
  if true ; then
    if [ -f "$DATABASE_ROLLBACK_VERSIONFILE" ] ; then
      rollback_ver="$(cat "$DATABASE_ROLLBACK_VERSIONFILE")"
      echo "----------------------- Do rollback to version $rollback_ver"
      logExe "$DATABASE_MIGRATOR" \
       $AUX_ARGS \
       --source "file://$DATABASE_MIGRATIONS_OLD" \
       --database.address "$DATABASE_HOST:$DATABASE_PORT" \
       --database.name "$DATABASE_NAME" \
       --database.user "$DATABASE_USER" \
       --database.password "$DATABASE_PASSWORD" \
       goto $rollback_ver
      echo "----------------------- Done rollback to version $rollback_ver."
    fi
    #
    echo "----------------------- Do migrate to version $DATABASE_VERSION"
    logExe "$DATABASE_MIGRATOR" \
     $AUX_ARGS \
     --source "file://$DATABASE_MIGRATIONS" \
     --database.address "$DATABASE_HOST:$DATABASE_PORT" \
     --database.name "$DATABASE_NAME" \
     --database.user "$DATABASE_USER" \
     --database.password "$DATABASE_PASSWORD" \
     goto $DATABASE_VERSION
    echo "----------------------- Done migrate to version $DATABASE_VERSION."
  fi
  #
  if true ; then
    if [[ $1 == force ]] ; then
      logExe "$DATABASE_DBTOOL" post-force
    else
      logExe "$DATABASE_DBTOOL" post
    fi
  fi
  #
  logFinish
}

# --------------------------------------------------------------------------------------------------------------------------------


if [[ $DATABASE_LOGLEVEL == debug ]] ; then
  dump_vars
  AUX_ARGS+="--verbose"
fi

if $DATABASE_FORCE ; then
  exec_migration force
else
  exec_migration
fi


