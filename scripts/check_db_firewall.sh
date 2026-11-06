#!/bin/bash
set -euo pipefail
namespace=library-firewall-check
if ip netns list | grep -q "^${namespace} "; then
  echo 'Test namespace already exists; refusing to replace it' >&2
  exit 1
fi
ip netns add "$namespace"
trap 'ip netns delete "$namespace"' EXIT
ip link add outsider link enp0s8 type ipvlan mode l2
ip link set outsider netns "$namespace"
ip -n "$namespace" addr add 192.168.77.99/24 dev outsider
ip -n "$namespace" link set outsider up
ip -n "$namespace" link set lo up
ip netns exec "$namespace" python3 - <<'PY'
import socket
with socket.socket() as client:
    client.settimeout(3)
    try:
        client.connect(('192.168.77.11', 5432))
    except (TimeoutError, ConnectionRefusedError):
        print('PASS: database denied to independent network namespace 192.168.77.99')
    else:
        raise SystemExit('FAIL: database reachable from unauthorized address')
PY
