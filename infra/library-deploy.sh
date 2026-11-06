#!/bin/bash
set -euo pipefail
sha=${1:?Commit SHA required}
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid SHA' >&2; exit 1; }
exec 9>/var/lock/library-deploy.lock
flock -n 9 || { echo 'Deployment already in progress' >&2; exit 1; }
cd /opt/library-deploy
git fetch origin "$sha"
git switch --detach "$sha"
export APP_IMAGE="127.0.0.1:5000/library:$sha" APP_VERSION="$sha"
compose=(docker compose --env-file /etc/library/container.env -f compose.yaml -f compose.registry.yaml)
"${compose[@]}" up -d registry
archive="/var/lib/library/releases/$sha/image.tar.gz"
if [[ -f "$archive" ]]; then
    gzip -dc "$archive" | docker load
    docker image inspect "ghcr.io/kolloko2/library-api-lab1:$sha" >/dev/null
    docker tag "ghcr.io/kolloko2/library-api-lab1:$sha" "$APP_IMAGE"
    docker push "$APP_IMAGE"
fi
"${compose[@]}" pull app migrate
"${compose[@]}" up -d --no-build --scale app=2 --wait --wait-timeout 180
"${compose[@]}" exec -T nginx nginx -s reload
/opt/library/.venv/bin/python scripts/release_check.py http://127.0.0.1:8080 "$sha"
printf '%s\n' "$sha" > /var/lib/library/deployed-sha
echo "Accepted release $sha"
