# Security policy

Please report security issues privately through GitHub Security Advisories for this repository. Do not open a public issue containing credentials, spreadsheet IDs, Bluetooth addresses, attendance data, or dashboard tokens.

The dashboard binds to `127.0.0.1` by default. Binding it to a LAN address requires `INOUT_DASHBOARD_TOKEN`. Put TLS and authentication in a reverse proxy if it must be available beyond a trusted local network.
