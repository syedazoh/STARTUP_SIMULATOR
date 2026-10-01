#!/usr/bin/env bash
# Run this ON the EC2 host, from the directory containing docker-compose.prod.yml
# and .env (see docs/deployment.md for the one-time setup that puts them there).
# Jenkins' "Deploy to EC2" stage SSHes in and runs this same sequence.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker image prune -f

echo "Deployed. Verify: curl https://\${APP_DOMAIN}/health  (via the caddy TLS terminator)"
