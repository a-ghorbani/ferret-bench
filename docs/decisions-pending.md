# Pending decisions (repo packaging)

## 1. `cache/` and `runs/` are tracked, but `.gitignore` says they should not be

`.gitignore` has listed both since `c6282c3`, but they were already tracked and gitignore
does not untrack. Today they are ~85% of tracked files (`cache/` 375 MB / 4,979 files,
`runs/` 126 MB / 583 files) and `.git` is 69 MB. **The repo currently contradicts itself**,
and a contributor cannot tell which policy is real.

These are two different decisions, not one:

**`cache/` — recommend untracking.** It is not the reproducibility asset it looks like. It is
keyed on model-generated queries with no TTL, and entries were captured across different days,
which is precisely the confound recorded in `FINDINGS-2026-07-22-measurement-precision.md`
(cache-hit rate rose 6%→58% with run order). Shipping it implies a determinism guarantee it
cannot honour.

**`runs/` — do not simply delete.** Every published claim is checkable only against these, and
that is how the `0.00` gate-failure error was caught. Untrack only alongside a durable
alternative: a GitHub release tarball with its checksum recorded in the README.

**Note that `git rm -r --cached` alone is cosmetic.** It stops future tracking but leaves the
objects in history, so `.git` stays 69 MB and clones stay slow. Getting the real benefit needs
`git filter-repo` and a force-push, which **breaks every existing clone and fork**. The repo
is public at `a-ghorbani/ferret-bench`, so this is an owner decision. If it is done, do it
soon — the cost only grows.

Whichever way it goes, make `.gitignore`, the README and the tree agree.

## 2. Package layout

`harness/` is not installable; ~15 modules use `sys.path.insert` and the supported entry point
is `cd harness && python3 <script>.py`. Converting to a real package with console entry points
removes a whole class of contributor friction, but it touches every module and every documented
command, so it deserves its own PR rather than being folded into unrelated work. Listed as a
good-first-contribution in `CONTRIBUTING.md`.

## 3. Housekeeping

- `runs/20260722-154358-swaptest-*` is an aborted 26-item smoke test. Its manifest is marked
  `"aborted": true` so it stops crashing `aggregate.py`, but it should be deleted — it will
  otherwise appear as a bogus row in aggregate output.
