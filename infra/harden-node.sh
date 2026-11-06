#!/bin/bash
set -euo pipefail
test -s /home/devops/.ssh/authorized_keys
install -m 0644 /opt/library/infra/sshd-library.conf /etc/ssh/sshd_config.d/library.conf
/usr/sbin/sshd -t
systemctl reload ssh
systemctl set-default multi-user.target
export DEBIAN_FRONTEND=noninteractive
apt-get purge -y -qq lightdm xfce4 xfce4-session xfdesktop4 xfwm4
echo 'Graphical login removed; root and password SSH login disabled'
