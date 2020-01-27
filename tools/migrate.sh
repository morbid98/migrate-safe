#!/bin/bash

dir="$(dirname "$0")/../tmp"
dir="$(readlink -e "$dir")"
if [ -z "$dir" ] ; then
  echo "Working dir is invalid" >&2
  exit 3
fi

mig="$dir/migrate"
if [ ! -x "$mig" ] ; then
  echo "Migrate have not found at: $mig" >&2
  exit 3
fi
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$dir
#ldd "$mig"
"$mig" "$@"
