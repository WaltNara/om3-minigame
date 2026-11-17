"""Loader and shared helpers for the combined Games firmware manifest.

The manifest configures build/test/package operations and inventories the
games. Native linking and dispatch remain explicit in the composer/host code.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / 'games.json'


def load(path=MANIFEST):
    """Read and validate games.json. Raises ValueError on any inconsistency."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    validate(data)
    return data


def validate(data):
    if data.get('schema') != 1:
        raise ValueError('unsupported manifest schema')
    games = data['games']
    ids = [g['id'] for g in games]
    states = [g['state_id'] for g in games]
    if not games or len(ids) != len(set(ids)):
        raise ValueError('game ids must be unique and non-empty')
    if len(states) != len(set(states)):
        raise ValueError('game state ids must be unique')
    reserved = {data['launcher']['state_closed'], data['launcher']['state_menu']}
    if reserved & set(states):
        raise ValueError('game state ids collide with launcher states')
    entries = data['launcher']['entries']
    if data['launcher']['back_index'] != len(entries) - 1:
        raise ValueError('back_index must be the last launcher entry')
    if [g['title'] for g in games] != entries[:len(games)]:
        raise ValueError('launcher entries must start with the game titles')
    for game in games:
        if data['launcher']['state_ids'].get(game['id']) != game['state_id']:
            raise ValueError('state_ids must agree with each game: ' + game['id'])
    missing = [p for p in required_paths(data) if not (ROOT / p).exists()]
    if missing:
        raise ValueError('manifest paths do not exist: ' + ', '.join(missing))
    names = [name for name, _ in evidence_files(data)]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError('evidence archive names collide: ' + ', '.join(duplicates))


def path(data, relative):
    """Resolve a manifest-relative path against the project root."""
    return ROOT / relative


def required_paths(data):
    """Paths that must exist before a build (generated outputs excluded)."""
    out = [data['image']['builder'],
           *data['source_dependencies'], *data['documentation'],
           data['launcher']['launcher_assets'],
           *data['launcher']['host_sources'],
           *data['docs'], *data['validation']['tests']]
    for game in data['games']:
        out += game.get('sources', [])
        out += game.get('assets', [])
        out += game.get('tests', [])
        out += game.get('support_sources', [])
    return sorted(set(out))


def source_paths(data):
    """Every source-like file whose hash belongs in the build evidence."""
    out = [*data['source_dependencies'], *data['validation']['tests'], data['image']['builder'], data['launcher']['launcher_assets'],
           *data['launcher']['host_sources']]
    for game in data['games']:
        out += game.get('sources', [])
        out += game.get('assets', [])
        out += game.get('tests', [])
        out += game.get('support_sources', [])
    return sorted(set(out))


def tests(data):
    """Current release validation commands, deduplicated in declared order."""
    return list(dict.fromkeys(data['validation']['tests']))


def validation_reports(data):
    """(archive name, absolute path) pairs for all validation reports."""
    seen, out = set(), []
    for game in [data['validation']]:
        for rel in game.get('reports', []):
            if rel in seen:
                continue
            seen.add(rel)
            p = Path(rel)
            # Keep the parent directory so two games' validation.json files
            # never collide inside the package's evidence folder.
            name = (p.parent.name + '-validation.json' if p.name == 'validation.json'
                    else p.name)
            out.append((name, path(data, rel)))
    return out


def evidence_files(data):
    """(archive name, absolute path) pairs shipped into evidence/."""
    out = [(Path(rel).name, path(data, rel))
           for game in data['games'] for rel in game.get('evidence', [])]
    out += [(Path(rel).name, path(data, rel)) for rel in data['shared_evidence']]
    out += [(Path(rel).name, path(data, rel)) for rel in data['generated_sources_to_ship']]
    out += [(Path(rel).name, path(data, rel)) for rel in data['docs']]
    out += validation_reports(data)
    return out


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def source_hashes(data):
    return {rel: sha256(path(data, rel)) for rel in source_paths(data)}


def check_report(report, digest):
    """Accept native report formats, but never infer a missing image hash."""
    status = report.get('status', '')
    if status not in ('passed', 'PASS emulator only', 'PASS emulator native application/GUI protocol'):
        raise ValueError('validation not passed: ' + str(status))
    hashes = [report[k] for k in ('image_sha256', 'candidate_sha256') if k in report]
    if not hashes or any(value != digest for value in hashes):
        raise ValueError('validation report missing image hash or belongs to another image')


def check_sources(build):
    for rel, want in build['source_sha256'].items():
        if sha256(ROOT / rel) != want:
            raise ValueError('source changed since build: ' + rel)


def game_summary(data):
    return [{'id': g['id'], 'title': g['title'], 'state_id': g['state_id'],
             'buffer': g['buffer'], 'sources': g.get('sources', []),
             'tests': g.get('tests', []),
             'validation': g.get('validation', []),
             'known_issues': g.get('known_issues', [])}
            for g in data['games']]


def image_path(data):
    return path(data, f"{data['image']['output_dir']}/{data['image']['main_image']}")


def metadata_path(data):
    return path(data, f"{data['image']['output_dir']}/{data['image']['bundle_metadata']}")
