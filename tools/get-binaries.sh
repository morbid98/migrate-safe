#!/bin/bash -xe

mkdir -p tmp

dir="tmp"
dir="$(readlink -e "$dir")"

docker rm tmp-migrate || true
docker create --name tmp-migrate infoblox/migrate
docker cp tmp-migrate:/lib/libc.musl-x86_64.so.1 tmp/
docker cp tmp-migrate:/lib/ld-musl-x86_64.so.1 tmp/
docker cp tmp-migrate:/migrate tmp/
docker rm tmp-migrate

sudo chown $USER tmp/*.so.1 tmp/migrate

tmp/patchelf --set-interpreter "$dir/ld-musl-x86_64.so.1" "$dir/migrate"
