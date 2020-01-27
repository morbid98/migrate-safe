#!/bin/bash

mkdir -p tmp
cd tmp

git clone https://github.com/NixOS/patchelf patchelf.git
cd patchelf.git

./bootstrap.sh
./configure
make
cp src/patchelf ../../tmp/
