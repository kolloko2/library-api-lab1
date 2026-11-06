#!/bin/sh
set -eu
cd /opt/library
: "${APP_IMAGE:?Set immutable image SHA tag}"
: "${APP_VERSION:?Set expected commit SHA}"
exec 9>/var/lock/library-deploy.lock
flock -n 9 || exit 1
docker compose pull
docker compose up -d --no-build --wait --wait-timeout 180
python3 scripts/release_check.py "http://127.0.0.1:8080" "$APP_VERSION"
