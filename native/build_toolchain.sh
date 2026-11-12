#!/usr/bin/env bash
set -euo pipefail
cd /d/om3-minigames/work
export PATH=/d/mingw64/bin:/d/Git/usr/bin:$PATH
if [ ! -d binutils-2.42 ]; then
  tar -xJf binutils_2.42.orig.tar.xz
fi
cd toolchain
if [ ! -f Makefile ]; then
  ../binutils-2.42/configure --build=x86_64-w64-mingw32 --host=x86_64-w64-mingw32 --target=mn10300-elf \
    --disable-nls --disable-werror --disable-gdb --disable-sim --disable-gprof --disable-gold \
    --disable-libctf --disable-gprofng --disable-shared >configure.log 2>&1
fi
/d/om3-minigames/work/msys-tools/usr/bin/make.exe -j8 MAKEINFO=true all-gas all-ld all-binutils >make.log 2>&1
