#!/usr/bin/env bash
# Package the local runs/ tree as a downloadable evidence snapshot and (optionally) publish it.
#
# WHY THIS IS A LOCAL SCRIPT, NOT CI: runs/ is deliberately untracked (see
# docs/decisions-pending.md), so it exists only on the machine that produced it. A GitHub
# Actions runner would clone the repo and find no runs/ to package. The release therefore
# must be cut from a workstation that has the data — this script is that step.
#
# Usage:
#   scripts/release-runs.sh                 # build tarball + checksum only (no upload)
#   scripts/release-runs.sh --publish       # also create the GitHub release (needs gh auth)
#
# gh only UPLOADS; it never builds archives. This script builds runs-<date>.tar.gz next to
# the repo, writes its .sha256, and leaves both there. --publish then attaches them to a
# release tagged runs-<date>.
set -euo pipefail
cd "$(dirname "$0")/.."                       # repo root
REPO_ROOT="$(pwd)"
REPO_SLUG="a-ghorbani/ferret-bench"

[ -d runs ] || { echo "no runs/ here — nothing to package"; exit 1; }

DATE="$(date +%Y%m%d)"
TAG="runs-${DATE}"
OUT_DIR="$(cd .. && pwd)"                     # sibling of the repo, so the archive is never inside runs/
TARBALL="${OUT_DIR}/ferret-bench-runs-${DATE}.tar.gz"

echo "packaging runs/ -> ${TARBALL}"
# Exclude aborted smoke-test runs (manifest marks them) and python caches.
tar --exclude='runs/*swaptest*' --exclude='**/__pycache__' \
    -C "${REPO_ROOT}" -czf "${TARBALL}" runs

sha256sum "${TARBALL}" | tee "${TARBALL}.sha256"
N=$(tar -tzf "${TARBALL}" | grep -c 'manifest.json' || true)
SIZE=$(du -h "${TARBALL}" | cut -f1)
echo "  ${N} run dirs, ${SIZE}"

if [ "${1:-}" != "--publish" ]; then
  echo
  echo "built only. to publish:"
  echo "  scripts/release-runs.sh --publish"
  echo "or attach manually at https://github.com/${REPO_SLUG}/releases/new?tag=${TAG}"
  exit 0
fi

command -v gh >/dev/null || { echo "gh not installed; upload ${TARBALL} via the web UI"; exit 1; }
echo "creating release ${TAG} on ${REPO_SLUG} ..."
gh release create "${TAG}" "${TARBALL}" "${TARBALL}.sha256" \
  --repo "${REPO_SLUG}" \
  --title "Run evidence — ${DATE}" \
  --notes "Full \`runs/\` tree backing every published number (${N} run dirs).

Extract at the repo root:
\`\`\`
tar -xzf $(basename "${TARBALL}")
\`\`\`
Verify: \`sha256sum -c $(basename "${TARBALL}").sha256\`

\`cache/\` is not shipped — it regenerates on first run (replay-or-live)."
echo "done: https://github.com/${REPO_SLUG}/releases/tag/${TAG}"
