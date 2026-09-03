# In-Out Tracker

[日本語](README.ja.md)

In-Out Tracker is a Raspberry Pi attendance logger. It scans for configured Bluetooth devices and records the first and latest sightings of each day in Google Sheets. It also includes a small local dashboard for finding and registering devices.

## Important iPhone limitation

iOS does not guarantee that an iPhone continuously advertises a stable Bluetooth address. A normal iPhone may only appear while discoverable, paired, connected, or advertising through a compatible beacon app. Test detection before relying on this for payroll or safety decisions. A dedicated BLE beacon is usually more reliable.

## Features

- Python 3.9 or newer, BlueZ, and service-account based Google authentication
- One Bluetooth scan per polling cycle, with an absence grace period
- Automatic clean monthly sheet creation or optional in-workbook template duplication
- Per-device error isolation, retry backoff, structured logs, and persistent presence state
- Local responsive dashboard with token enforcement for non-localhost binding
- systemd units, validation command, tests, and English/Japanese documentation

## Quick start

Requirements: Raspberry Pi OS with Bluetooth, Python 3.9 or newer, a Google Cloud project, and a Google service account.

```bash
git clone https://github.com/naoi/inout.git
cd inout
sudo ./INSTALL.sh
sudoedit /var/lib/inout/config.yaml
sudo -u inout /opt/inout/venv/bin/inout --config /var/lib/inout/config.yaml check-config
sudo systemctl enable --now inout inout-dashboard
```

The installer does not start services until you finish the configuration and access check.

Open the dashboard from the Pi itself at <http://127.0.0.1:8080>. For SSH access, forward it without exposing the port:

```bash
ssh -L 8080:127.0.0.1:8080 pi@raspberrypi.local
```

Then open <http://127.0.0.1:8080> on your computer.

## Google Sheets setup

1. Enable Google Sheets API in a Google Cloud project.
2. Create a service account and download its JSON key.
3. Create one spreadsheet per person, or choose another layout that keeps each configured device mapped to a spreadsheet.
4. Share each spreadsheet with the service account email as Editor.
5. Put the JSON key at `/etc/inout/google-service-account.json` with restrictive permissions.
6. Copy [config.example.yaml](config.example.yaml) to `/var/lib/inout/config.yaml` and enter the Bluetooth address and spreadsheet ID.

The application creates a clean `YYYY-MM` tab automatically. To keep an existing layout, set `template_sheet_id` to a tab ID in the same target spreadsheet. New users should omit this setting.

The historical spreadsheet referenced by the original project is not used as a public template because it contains unrelated historical tabs and broken formula references. See [Google Sheets design](docs/google-sheets.md).

## Commands

```bash
inout --config /var/lib/inout/config.yaml check-config
inout --config /var/lib/inout/config.yaml scan
inout --config /var/lib/inout/config.yaml run --once
inout --config /var/lib/inout/config.yaml run
inout --config /var/lib/inout/config.yaml dashboard
```

## Documentation

- [Installation and configuration](docs/setup.md)
- [Dashboard and device registration](docs/dashboard.md)
- [Google Sheets layout](docs/google-sheets.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Hardware and Google calls are isolated behind small interfaces, so unit tests run without Bluetooth hardware or Google credentials.

## License

MIT
