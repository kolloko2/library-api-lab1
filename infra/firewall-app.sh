#!/bin/sh
set -eu
: "${ADMIN_CIDR:?Set trusted admin CIDR}"
iptables -N LIBRARY_INPUT 2>/dev/null || true
iptables -F LIBRARY_INPUT
iptables -A LIBRARY_INPUT -i lo -j ACCEPT
iptables -A LIBRARY_INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A LIBRARY_INPUT -p tcp -s "$ADMIN_CIDR" --dport 22 -j ACCEPT
iptables -A LIBRARY_INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A LIBRARY_INPUT -j DROP
iptables -C INPUT -j LIBRARY_INPUT 2>/dev/null || iptables -I INPUT 1 -j LIBRARY_INPUT
iptables-save > /etc/iptables/rules.v4
