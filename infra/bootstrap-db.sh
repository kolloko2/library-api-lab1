#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
hostnamectl set-hostname library-db
systemctl set-default multi-user.target
systemctl disable --now lightdm || true
apt-get update -qq
apt-get install -y -qq postgresql postgresql-client iptables-persistent
if ! nmcli con show devops-backend >/dev/null 2>&1; then
  nmcli con add type ethernet ifname enp0s8 con-name devops-backend ipv4.method manual ipv4.addresses 192.168.77.11/24 ipv6.method disabled
fi
nmcli con up devops-backend
nmcli con modify devops-backend connection.autoconnect-priority 100
nmcli con modify devops-nat connection.autoconnect-priority 100
nmcli con modify Lab connection.autoconnect no 2>/dev/null || true
nmcli con modify Management connection.autoconnect no 2>/dev/null || true
systemctl enable --now postgresql
echo 'Database host packages and static network configured'
