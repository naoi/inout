#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo: sudo ./INSTALL.sh" >&2
  exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/inout"
CONFIG_DIR="/etc/inout"
STATE_DIR="/var/lib/inout"

apt-get update
apt-get install -y bluetooth bluez python3 python3-venv

if ! getent group inout >/dev/null 2>&1; then
  groupadd --system inout
fi
if ! id inout >/dev/null 2>&1; then
  useradd --system --gid inout --home-dir "${STATE_DIR}" --create-home --groups bluetooth inout
else
  usermod --append --groups bluetooth inout
fi

install -d -m 0755 "${INSTALL_DIR}"
install -d -m 0750 -o root -g inout "${CONFIG_DIR}"
install -d -m 0750 -o inout -g inout "${STATE_DIR}"
python3 -m venv "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install "${SOURCE_DIR}"

if [[ ! -e "${STATE_DIR}/config.yaml" ]]; then
  install -m 0600 -o inout -g inout "${SOURCE_DIR}/config.example.yaml" "${STATE_DIR}/config.yaml"
fi

install -m 0644 "${SOURCE_DIR}/systemd/inout.service" /etc/systemd/system/inout.service
install -m 0644 "${SOURCE_DIR}/systemd/inout-dashboard.service" /etc/systemd/system/inout-dashboard.service
systemctl daemon-reload

echo "Installed. Next:"
echo "  1. Edit /var/lib/inout/config.yaml"
echo "  2. Put the service account JSON at /etc/inout/google-service-account.json"
echo "  3. Run: sudo -u inout ${INSTALL_DIR}/venv/bin/inout --config ${STATE_DIR}/config.yaml check-config"
echo "  4. Enable services when the check succeeds:"
echo "     systemctl enable --now inout inout-dashboard"
