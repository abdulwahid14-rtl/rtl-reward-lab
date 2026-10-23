#!/usr/bin/env bash
# Fetch the verilog-eval dataset at the commit pinned in
# provenance/verilogeval-commit.txt. The dataset isn't vendored into this
# repo (see .gitignore); run this once after cloning, before using any task
# that lives under third_party/verilog-eval/ (e.g. popcount3).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/third_party/verilog-eval"
REMOTE_URL="https://github.com/NVlabs/verilog-eval.git"
PINNED_COMMIT="$(cat "$REPO_ROOT/provenance/verilogeval-commit.txt")"

if [ -d "$DEST/.git" ]; then
  CURRENT_COMMIT="$(git -C "$DEST" rev-parse HEAD)"
  if [ "$CURRENT_COMMIT" = "$PINNED_COMMIT" ]; then
    echo "third_party/verilog-eval already at pinned commit $PINNED_COMMIT"
    exit 0
  fi
  echo "third_party/verilog-eval exists but is at $CURRENT_COMMIT, expected $PINNED_COMMIT" >&2
  echo "remove $DEST and re-run this script if you want it re-cloned" >&2
  exit 1
fi

echo "Cloning verilog-eval into $DEST"
git clone "$REMOTE_URL" "$DEST"
echo "Checking out pinned commit $PINNED_COMMIT"
git -C "$DEST" checkout "$PINNED_COMMIT"
