#!/bin/sh
# Install Tanakh Reader git hooks into .git/hooks/.
# Run from the repo root: bash validators/hooks/install.sh

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

cp validators/hooks/pre-commit  .git/hooks/pre-commit
cp validators/hooks/commit-msg  .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg

echo "Installed: .git/hooks/pre-commit, .git/hooks/commit-msg"
