# Packaging decisions

## 1. `cache/` and `runs/` — RESOLVED 2026-07-23

Both were tracked while `.gitignore` said they shouldn't be — ~85% of tracked files, `.git` was 69 MB. Resolved:

- **`cache/`** — dropped from tracking and purged from all history. Regenerable replay data, keyed on stale model-generated queries with no TTL, so not the durability asset it looked like. Regenerates on first run.
- **`runs/`** — untracked and purged from history, but preserved as a release asset (`ferret-bench-runs-<date>.tar.zst`, sha256 in release notes) because every published claim is checkable against it.
- History rewritten with `git filter-repo`; `.git` 69 MB → 1.4 MB. Full pre-rewrite backup bundle kept outside the repo (`ferret-bench-backup-<ts>.bundle`).
- `.gitignore`, the tree and history now agree: both dirs ignored, none tracked, none in history.

## 2. Package layout — OPEN

`harness/` is not installable; ~15 modules use `sys.path.insert` and the supported entry point is `cd harness && python3 <script>.py`. Converting to a real package with console entry points removes a class of contributor friction but touches every module and every documented command, so it deserves its own PR. Listed as a good-first-contribution in `CONTRIBUTING.md`.

## 3. Housekeeping — OPEN

- `runs/20260722-154358-swaptest-*` is an aborted 26-item smoke test (manifest marked `"aborted": true` so it no longer crashes `aggregate.py`). Delete when convenient; already excluded from the runs release tarball.
- `harness/export_site.py` is superseded by `study-1/export_site.py` (forked, ~70 of ~290 lines shared). Merge and delete the old one.
