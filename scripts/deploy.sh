#!/bin/sh
# Run from any directory. Re-running preserves secrets and persistent volumes.
set -eu
cd "$(dirname "$0")/.."
docker compose version >/dev/null
if [ -e .git ]; then
    git submodule sync --recursive
    git submodule update --init --recursive
fi
# Deploy-button projects have independent child repositories after detaching
# the template's history. Both kinds of checkout use the same Compose stack.
test -f apps/unicom/models/__init__.py
test -f apps/unibot/models.py
if [ ! -f .env ]; then
    (umask 077; cp .env.example .env)
fi
python3 scripts/configure_env.py .env
docker compose up -d --build --wait --wait-timeout 180
