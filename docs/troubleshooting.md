# Troubleshooting

## `bluetoothctl was not found`

Install BlueZ with `sudo apt-get install bluez bluetooth` and check `systemctl status bluetooth`.

## The iPhone appears once but not continuously

This is expected for many iOS configurations. Keep Settings > Bluetooth open for a discovery test. For unattended operation, pair/connect the phone if practical or use a dedicated BLE beacon with a stable identity. Do not increase scan frequency until detection reliability is measured.

## `Permission denied` from BlueZ

Confirm the service user belongs to the `bluetooth` group with `id inout`, then restart the service after changing group membership.

## Google returns 403

Confirm that Google Sheets API is enabled and the target spreadsheet is shared with the `client_email` in the service account JSON as Editor. Run `inout ... check-config` again.

## The current month cannot be created

If `template_sheet_id` is set, confirm that the tab ID exists inside that same spreadsheet. Remove the setting to use the clean built-in layout.

## A time was not recorded

Check `journalctl -u inout` for a per-device error. The service keeps scanning other devices if one Sheets update fails. It retries on the next successful sighting, and column C remains the first successfully written time while D advances.
