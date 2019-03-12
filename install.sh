#!/bin/bash

# Updated by yas 2019/03/11.
# Created by yas 2019/03/01.

export TOTAL=$(( $(grep 'echo_count' $0 | wc -l)-2 ))
export COUNT=1

function echo_count () {

  echo -n "($(( COUNT++ ))/${TOTAL}) $1"
}

export CLIENT_ID=
export PROJECT_ID=
export CLIENT_SECRET=

echo
echo_count 'Making .credentials directory... '
if [ ! -e ~/.credentials/ ]; then
  mkdir -p /.credentials/
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
sudo apt -y install python-bluez python-pip; sudo pip install --upgrade oauth2client google-api-python-client

echo
echo 'Setting up inout.service... '
cd scripts
if [ ! -e /usr/bin/inout.py ]; then
  sudo ln -s inout.py /usr/bin/
fi
echo 'Done'

echo
echo_count 'Creating client_secret.json... '
sudo cat << CLIENT_SECRET > client_secret.json
{"installed":{"client_id":"${CLIENT_ID}","project_id":"${PROJECT_ID}","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"${CLIENT_SECRET}","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
CLIENT_SECRET

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
echo 'Done.'

echo
echo 'Manually run: ./inout.py --noauth_local_webserver'
./inout.py --noauth_local_webserver

echo
echo "Done: '$(basename $0)'"
echo