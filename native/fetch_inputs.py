"""Fetch official firmware and GNU source for the local native experiment."""
import hashlib
import json
import pathlib
import sys
import urllib.request
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / 'work'
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
sys.path.insert(0, str(ROOT / 'vendor/caduceus-om3/firmware'))
import patch

if sys.argv[1] == 'stock':
    dest = WORK / patch.STOCK_NAME
    spec = json.loads((ROOT / 'vendor/caduceus-om3/releases/v0.26.2/patch.json').read_text())
    if not dest.exists():
        data = patch.fetch_stock(spec['stock_size'])
        assert hashlib.sha256(data).hexdigest() == spec['stock_sha256']
        dest.write_bytes(data)
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == spec['stock_sha256']
    print('Verified official OM-3 1.1:', dest)
elif sys.argv[1] == 'binutils':
    dest = WORK / 'binutils_2.42.orig.tar.xz'
    if not dest.exists():
        with urllib.request.urlopen('https://archive.ubuntu.com/ubuntu/pool/main/b/binutils/binutils_2.42.orig.tar.xz', timeout=60) as response:
            dest.write_bytes(response.read())
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == 'f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800'
    print('Verified GNU binutils source:', dest)
elif sys.argv[1] == 'make':
    dest = WORK / 'make-4.4.1-2-x86_64.pkg.tar.zst'
    urllib.request.urlretrieve('https://repo.msys2.org/msys/x86_64/' + dest.name, dest)
    target = WORK / 'msys-tools'
    target.mkdir(exist_ok=True)
    subprocess.run(['C:/Windows/System32/tar.exe', '-xf', str(dest), '-C', str(target)], check=True)
    print('MSYS make extracted locally:', target)
