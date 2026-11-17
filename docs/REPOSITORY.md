# Repository organization

The supplied HTML review correctly found a four-game default behind a five-game
README, incompatible validation formats, and packaging that required ignored
notes. The current `build/` workflow fixes these together.

Tests moved to `tests/`, diagnostics to `tools/diagnostics/`, historical standalone
builders/packagers to `tools/legacy/`, and public docs to `docs/`. The HTML is kept
locally in ignored `docs/research/repository-review.html`.

Native assembly/assets stay together. Splitting every game or replacing checked
host generation would add firmware risk without fixing the immediate workflow.
The manifest configures release operations; it is not an automatic game linker.
A dispatcher refactor should be a separate tested change.

Historical tools are reference material, not supported release commands. The
sealed r5 release includes its original source snapshot for exact reproduction.
Current commands are in DEVELOPMENT.md; hardware/release facts are in STATUS.md.

CI checks syntax, tracked paths, local Markdown links, manifest consistency,
strict validation-report handling, and desktop rules. Native tests require local
dependencies; CI does not claim camera coverage or download firmware.

## Validation of this reorganization

- The reorganized native build produces exactly the accepted r5 raw SHA256.
- Public syntax/link/path checks and four report/package-documentation tests pass.
- Five desktop rule tests pass, including in a source-only export with no local
  dependencies or generated evidence.
- Camera-tested native code is unchanged. The current suite passed 181 touch
  events/replies, 1,750 physics cases, 26 render frames, seven GUI scenarios and
  14 outside-game snapshots. Unified packaging preflight passed with current
  public source/documentation paths and external-input hashes.
- Accepted r5 ZIP/rollback were preserved; this change does not install firmware.
