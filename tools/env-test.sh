#!/bin/bash

source .env

export "PATH=$PATH:$(readlink -e $(pwd)/bin)"

mkdir -p "$DATABASE_MIGRATIONS_OLD"

"$@"
