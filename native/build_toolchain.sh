#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root/work"
if [ ! -d binutils-2.42 ]; then
  tar -xJf binutils_2.42.orig.tar.xz
fi
mkdir -p toolchain
cd toolchain
if [ ! -f Makefile ]; then
  ../binutils-2.42/configure --target=mn10300-elf \
    --disable-nls --disable-werror --disable-gdb --disable-sim --disable-gprof --disable-gold \
    --disable-libctf --disable-gprofng --disable-shared >configure.log 2>&1
fi
"${OM3_MAKE:-make}" -j"${OM3_JOBS:-8}" MAKEINFO=true all-gas all-ld all-binutils >make.log 2>&1
