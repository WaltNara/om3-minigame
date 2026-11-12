"""Apply only file-URL portability fixes to the local emulator checkout."""
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'work/om-emu/emu'
for name, up in [('host/blobs.mjs', '../../'), ('checks/lib/env.mjs', '../../../'), ('bin/run.mjs', '../../')]:
    p = root / name
    text = p.read_text(encoding='utf-8')
    old = "path.resolve(new URL('" + up + "', import.meta.url).pathname)"
    new = "fileURLToPath(new URL('" + up + "', import.meta.url))"
    if old in text:
        text = text.replace("import path from 'node:path';", "import path from 'node:path';\nimport { fileURLToPath } from 'node:url';")
        p.write_text(text.replace(old, new), encoding='utf-8')
        print('Windows path fix:', name)
