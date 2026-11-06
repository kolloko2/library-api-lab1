#!/bin/sh
set -eu
iptables-restore --noflush < /etc/iptables/library.v4
iptables -C INPUT -j LIBRARY_MANAGED 2>/dev/null || iptables -I INPUT 1 -j LIBRARY_MANAGED
