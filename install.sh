#!/bin/bash

# Created by yas 2019/03/01

export CLIENT_ID=
export PROJECT_ID=
export CLIENT_SECRET=

echo
echo 'Making .credentials directory...'
if [ ! -e ~/.credentials/ ]; then
  mkdir ~/.credentials/
fi

echo
echo 'Making /root/credentials directory...'
if [ ! -e /root/.credentials/ ]; then
  sudo mkdir /root/.credentials/
fi

echo
echo 'Update libraries to the latest ones...'
sudo apt -y update; sudo apt -y upgrade; sudo apt -y dist-upgrade; sudo apt -y autoremove; sudo apt -y autoclean
sudo apt -y install python-bluez python-pip; sudo pip install --upgrade oauth2client google-api-python-client

echo
echo 'Setting up inout.service...'
cd scripts
if [ ! -e /usr/bin/inout.py ]; then
  sudo ln -s inout.py /usr/bin/
fi

echo
echo 'Creating client_secret.json...'
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

sudo cp /tmp/inout.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start inout.service
sudo systemctl enable inout.service

echo
echo 'Done.'

echo
echo 'Manually run: ./inout.py --noauth_local_webserver'
./inout.py --noauth_local_webserver
