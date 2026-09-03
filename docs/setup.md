# Installation and configuration

## Raspberry Pi

Use a currently supported Raspberry Pi OS release. Confirm the adapter before installing:

```bash
bluetoothctl show
```

Run `sudo ./INSTALL.sh`. The script installs only the required OS packages, creates an unprivileged `inout` user, creates a virtual environment under `/opt/inout`, and installs two systemd units. It does not upgrade the operating system or start the application.

## Google credentials

1. Enable Google Sheets API in Google Cloud Console.
2. Create a service account and JSON key.
3. Share every target spreadsheet with the service account email as Editor.
4. Install the key securely:

```bash
sudo install -m 0640 -o root -g inout downloaded-key.json /etc/inout/google-service-account.json
```

Never commit the JSON key. Service account keys are secrets.

## Configuration

Edit `/var/lib/inout/config.yaml`, based on [config.example.yaml](../config.example.yaml).

| Setting | Meaning |
| --- | --- |
| `polling_interval_seconds` | Delay between completed scan cycles |
| `absence_grace_seconds` | Time before a missed device changes to absent |
| `bluetooth_scan_seconds` | Length of each BlueZ discovery scan |
| `state_file` | Persistent last-seen state |
| `google.credentials_file` | Service account JSON path |
| `dashboard.host` / `port` | Dashboard listener, localhost by default |
| `devices[].address` | Stable Bluetooth address to look for |
| `devices[].spreadsheet_id` | ID between `/d/` and `/edit` in a Sheets URL |
| `devices[].template_sheet_id` | Optional tab ID inside the same spreadsheet |

Validate before enabling services:

```bash
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml check-config
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml scan
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml run --once
sudo systemctl enable --now inout inout-dashboard
```

View logs with `journalctl -u inout -f` and `journalctl -u inout-dashboard -f`.
