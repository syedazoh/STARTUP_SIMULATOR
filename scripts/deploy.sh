#!/usr/bin/env bash
# Operator/Jenkins invocation only, after backup, secrets and exact volumes are verified.
set -euo pipefail
cd "$(dirname "$0")/.."
for image in "${BACKEND_IMAGE:-}" "${WORKER_IMAGE:-}" "${FRONTEND_IMAGE:-}" "${CADDY_IMAGE:-}"; do
  if [[ ! "$image" =~ :[a-f0-9]{40}$ ]]; then
    echo 'Release images must use immutable full-commit tags.' >&2
    exit 1
  fi
done
docker compose -f docker-compose.next.yml config --quiet
docker compose -f docker-compose.next.yml pull
docker compose -f docker-compose.next.yml up -d --wait --wait-timeout 180
# Keep previous images and all data volumes for rollback; never prune on deploy.
echo 'Containers are ready. Verify HTTPS /api/health, sign-in, ownership and the approved demo before promotion.'
