"""Source-only checks; no firmware, dependency imports, or generated outputs needed."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
import manifest


def main():
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    paths = {ROOT / n for n in names if (ROOT / n).is_file()}
    forbidden = [p for p in paths if p.suffix.lower() in ('.bin', '.zip', '.omsd', '.o', '.elf')]
    if forbidden:
        raise ValueError('generated binaries in public source: ' + str(forbidden))
    for p in paths:
        if p.suffix == '.py':
            ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
        if p.suffix == '.md':
            for target in re.findall(r'\]\(([^\s)]+)\)', p.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                linked = (p.parent / target.split('#')[0]).resolve()
                if linked not in paths:
                    raise ValueError(f'{p.relative_to(ROOT)} links to missing/unpublished file: {target}')
    data = manifest.load()
    for rel in manifest.required_paths(data):
        if ROOT / rel not in paths:
            raise ValueError('manifest input not published: ' + rel)
    assert data['image']['builder_args'] == ['--flappy-touch']
    assert data['image']['environment']['OM3_OUTPUT_DIR'] == data['image']['output_dir']
    assert data['image']['environment']['OM3_FLAPPY_BUILD'] == data['image']['output_dir']
    assert len(data['games']) == 5 and data['launcher']['state_ids']['flappy'] == 6
    print(f'PASS source syntax, Markdown links, manifest and published paths ({len(paths)} files)')


if __name__ == '__main__':
    main()
