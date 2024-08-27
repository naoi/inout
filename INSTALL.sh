#!/bin/bash

# Updated by yas 2021/11/10.
# Updated by yas 2021/11/09.
# Updated by yas 2019/04/04.
# Updated by yas 2019/03/11.
# Created by yas 2019/03/01.

export TOTAL=$(( $(grep 'echo_count' $0 | wc -l)-2 ))
export COUNT=1

function echo_count () {

  echo -n "($(( COUNT++ ))/${TOTAL}) $1"
}

export BASE_DIR="$(pwd)"
set -a; eval "$(cat ${BASE_DIR}/.env <(echo) <(declare -x))"; set +a;

echo
echo_count 'Making .credentials directory... '
if [ ! -e ~/.credentials/ ]; then
  mkdir -p ~/.credentials/
fi
echo 'Done'

echo
echo_count 'Making /root/credentials directory... '
if [ ! -e /root/.credentials/ ]; then
  sudo mkdir -p /root/.credentials/
fi
echo 'Done'

echo
echo_count 'Update libraries to the latest ones...'
echo
echo
sudo apt -y update; sudo apt -y upgrade; sudo apt -y dist-upgrade; sudo apt -y autoremove; sudo apt -y autoclean

echo
echo_count 'Installing Python-related libraries...'
echo
echo
sudo apt -y install python3-pip python3-bluez python3-yaml python3-boto3 python3-googleapi python3-google-auth-oauthlib dhcpd

echo
export CLIENT_SECRETS='client_secrets.json'
echo_count "Creating client_secrets.json '${CLIENT_SECRETS_JSON}'... "
sudo cat << CLIENT_SECRETS > "${CLIENT_SECRETS}"
{"installed":{"client_id":"${GAPPS_CLIENT_ID}","project_id":"${GAPPS_PROJECT_ID}","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"${GAPPS_CLIENT_SECRET}","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
CLIENT_SECRETS
echo 'Done'

echo
echo_count "Setting up 'inout.service' as a daemon... "
cd scripts
if [ ! -e /usr/bin/inout.py ]; then
  sudo rm -fr /usr/bin/inout.py
  sudo ln -s "inout.py" /usr/bin/
fi

sudo cat << INOUT_SERVICE > /tmp/inout.service
[Unit]
Description=In-Out Checker
After=systemd-timesyncd.service dhcpcd.service bluetooth.target hciuart.service
Requires=systemd-timesyncd.service dhcpcd.service bluetooth.target hciuart.service

[Service]
Type=simple
ExecStart=/usr/bin/inout.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
INOUT_SERVICE
echo 'Done'

echo
echo_count "Setting up 'inout.service'... "
sudo cp /tmp/inout.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start inout.service
sudo systemctl enable inout.service
echo 'Done'

echo
echo "Manually run this command by root: sudo $(pwd)/inout.py --noauth_local_webserver"
# sudo ./inout.py --noauth_local_webserver

echo
echo "Done: 'inout.service' ('$(basename $0)')"
echo