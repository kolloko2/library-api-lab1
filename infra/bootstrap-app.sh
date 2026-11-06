#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
hostnamectl set-hostname library-app
systemctl set-default multi-user.target
systemctl disable --now lightdm || true
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip postgresql-client git curl make iptables-persistent ca-certificates gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable' > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
id library >/dev/null 2>&1 || useradd --system --home /var/lib/library --shell /usr/sbin/nologin library
install -d -m 0750 -o library -g library /var/lib/library
install -d -m 0750 -o root -g library /etc/library
if ! nmcli con show devops-backend >/dev/null 2>&1; then
  nmcli con add type ethernet ifname enp0s8 con-name devops-backend ipv4.method manual ipv4.addresses 192.168.77.10/24 ipv6.method disabled
fi
nmcli con up devops-backend
echo 'Application host packages and static network configured'
