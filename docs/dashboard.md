# Dashboard

The dashboard lists registered devices, runs a nearby-device scan, and appends a selected Bluetooth address and Google Spreadsheet ID to the YAML configuration. It never asks for or displays Google credentials.

It listens on `127.0.0.1:8080` by default. Use SSH forwarding to reach it from another computer. This keeps the dashboard off the LAN.

If LAN binding is unavoidable, set a strong token and change the host:

```bash
sudo sh -c 'umask 077; printf "%s\n" "INOUT_DASHBOARD_TOKEN=replace-with-a-long-random-value" > /etc/inout/dashboard.env'
```

```yaml
dashboard:
  host: 0.0.0.0
  port: 8080
  token_env: INOUT_DASHBOARD_TOKEN
```

Restart the dashboard after changing configuration. The attendance service must also be restarted after registering a new device.

The `/api/health` endpoint is intentionally unauthenticated and returns only `{"status":"ok"}`. Other API routes require the token whenever it is configured.
