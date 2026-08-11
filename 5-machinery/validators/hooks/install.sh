#!/bin/sh
# Install Tanakh Reader git hooks into .git/hooks/.
# Run from anywhere: bash 5-machinery/validators/hooks/install.sh
#
# Sources are resolved from this script's own location rather than from a path
# spelled relative to the repo root. The 2026-08-10 reorg moved validators/ under
# 5-machinery/ and every hardcoded "validators/..." here went stale silently --
# the commit-msg hook died on a missing file, and the pre-commit gate's staged-path
# filter stopped matching, so it reported "docs-only" on commits full of .py files
# and skipped the baseline check entirely.

set -e

HOOK_SRC=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

cp "$HOOK_SRC/pre-commit"  .git/hooks/pre-commit
cp "$HOOK_SRC/commit-msg"  .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg

echo "Installed: .git/hooks/pre-commit, .git/hooks/commit-msg"
