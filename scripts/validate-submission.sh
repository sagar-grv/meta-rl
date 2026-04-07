#!/usr/bin/env bash
set -euo pipefail

PING_URL="${1:-}"
REPO_DIR="${2:-$(pwd)}"

if [ -z "$PING_URL" ]; then
  echo "Usage: validate-submission.sh <ping_url> [repo_dir]" >&2
  exit 1
fi

cd "$REPO_DIR"

echo "Running Docker build..."

if command -v python >/dev/null 2>&1; then
  python -m pytest -q
fi

if command -v openenv >/dev/null 2>&1; then
  openenv validate
fi

docker build -t support-queue-openenv .

echo "Checking Space ping..."
curl -fsS "$PING_URL" >/dev/null

echo "Validator completed successfully."
