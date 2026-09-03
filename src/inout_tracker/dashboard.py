from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .bluetooth import BluetoothctlScanner
from .config import DeviceConfig, add_device, load_config
from .errors import InOutError

MAX_BODY_BYTES = 64 * 1024

DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>In-Out Tracker</title><style>
:root{font-family:system-ui,sans-serif;color:#15202b;background:#f4f7f9}body{max-width:960px;margin:auto;padding:2rem}
h1{margin-bottom:.2rem}.muted{color:#5c6b76}.card{background:white;border-radius:12px;padding:1.2rem;margin:1rem 0;box-shadow:0 2px 10px #0001}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.65rem;border-bottom:1px solid #e6ebef}
label{display:block;margin:.6rem 0}input{box-sizing:border-box;width:100%;padding:.65rem;border:1px solid #bac5cd;border-radius:6px}
button{background:#1769aa;color:white;border:0;border-radius:6px;padding:.7rem 1rem;cursor:pointer}.row{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.ok{color:#087830}.error{color:#b42318}@media(max-width:640px){.row{grid-template-columns:1fr}}
</style></head><body><h1>In-Out Tracker</h1><p class="muted">Raspberry Pi Bluetooth attendance</p>
<section class="card"><h2>Registered devices</h2><button onclick="refresh()">Refresh</button><table><thead><tr><th>Name</th><th>Address</th><th>Sheet</th></tr></thead><tbody id="devices"></tbody></table></section>
<section class="card"><h2>Discover nearby devices</h2><button onclick="scan()">Scan for 8 seconds</button><p id="scanResult" class="muted"></p></section>
<section class="card"><h2>Register a device</h2><form id="form"><div class="row"><label>Name<input name="name" required></label><label>Bluetooth address<input name="address" placeholder="AA:BB:CC:DD:EE:FF" required></label></div><label>Google Spreadsheet ID<input name="spreadsheet_id" required></label><label>Template sheet ID (optional)<input name="template_sheet_id" inputmode="numeric"></label><label>Dashboard token (required for LAN access)<input id="token" type="password"></label><button>Register</button><p id="message"></p></form></section>
<script>
const headers=()=>{const token=document.querySelector('#token').value;return token?{'X-InOut-Token':token}:{}};
async function api(path,options={}){options.headers={...(options.headers||{}),...headers()};const r=await fetch(path,options);const j=await r.json();if(!r.ok)throw Error(j.error||r.statusText);return j}
async function refresh(){try{const data=await api('/api/devices');document.querySelector('#devices').innerHTML=data.devices.map(d=>`<tr><td>${escapeHtml(d.name)}</td><td><code>${escapeHtml(d.address)}</code></td><td><code>${escapeHtml(d.spreadsheet_id)}</code></td></tr>`).join('')}catch(e){show(e)}}
let found=[];async function scan(){const out=document.querySelector('#scanResult');out.textContent='Scanning...';try{const data=await api('/api/scan',{method:'POST'});found=data.devices;out.innerHTML=found.length?found.map(d=>`<button type="button" onclick="choose('${d.address}')">${escapeHtml(d.name)} (${d.address})</button>`).join(' '):'No devices found. Make the device discoverable and try again.'}catch(e){out.textContent=e.message}}
function choose(address){const d=found.find(item=>item.address===address);const f=document.querySelector('#form');f.address.value=address;f.name.value=d&&d.name!=='Unknown device'?d.name:''}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function show(e,ok=false){const m=document.querySelector('#message');m.textContent=e.message||e;m.className=ok?'ok':'error'}
document.querySelector('#form').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);const body=Object.fromEntries(f);if(!body.template_sheet_id)delete body.template_sheet_id;try{await api('/api/devices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});show('Registered. The service will use it on its next restart.',true);const token=document.querySelector('#token').value;e.target.reset();document.querySelector('#token').value=token;refresh()}catch(err){show(err)}});refresh();
</script></body></html>"""


def handler_factory(
    config_path: Path, scanner: BluetoothctlScanner
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "InOutDashboard/1.0"

        def _token_valid(self) -> bool:
            config = load_config(config_path)
            expected = os.getenv(config.dashboard.token_env, "")
            if not expected:
                return True
            supplied = self.headers.get("X-InOut-Token", "")
            return hmac.compare_digest(expected, supplied)

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _authorised(self) -> bool:
            if self._token_valid():
                return True
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "invalid dashboard token"})
            return False

        def do_GET(self) -> None:
            try:
                if self.path == "/":
                    body = DASHBOARD_HTML.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header(
                        "Content-Security-Policy", "default-src 'self' 'unsafe-inline'"
                    )
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path == "/api/health":
                    self._json(HTTPStatus.OK, {"status": "ok"})
                elif self.path == "/api/devices" and self._authorised():
                    config = load_config(config_path)
                    self._json(
                        HTTPStatus.OK,
                        {
                            "devices": [
                                {
                                    "name": item.name,
                                    "address": item.address,
                                    "spreadsheet_id": item.spreadsheet_id,
                                    "template_sheet_id": item.template_sheet_id,
                                }
                                for item in config.devices
                            ]
                        },
                    )
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except InOutError as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

        def do_POST(self) -> None:
            if not self._authorised():
                return
            try:
                if self.path == "/api/scan":
                    devices = scanner.discover()
                    self._json(
                        HTTPStatus.OK,
                        {
                            "devices": [
                                {"name": item.name, "address": item.address} for item in devices
                            ]
                        },
                    )
                    return
                if self.path != "/api/devices":
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY_BYTES:
                    self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid request size"})
                    return
                payload = json.loads(self.rfile.read(length))
                template = payload.get("template_sheet_id")
                device = DeviceConfig(
                    name=str(payload.get("name", "")).strip(),
                    address=str(payload.get("address", "")).strip().upper(),
                    spreadsheet_id=str(payload.get("spreadsheet_id", "")).strip(),
                    template_sheet_id=int(template) if template not in (None, "") else None,
                )
                add_device(config_path, device)
                self._json(HTTPStatus.CREATED, {"registered": device.address})
            except (InOutError, ValueError, TypeError, json.JSONDecodeError) as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def serve_dashboard(config_path: Path) -> None:
    config = load_config(config_path)
    scanner = BluetoothctlScanner(config.bluetooth_scan_seconds)
    server = ThreadingHTTPServer(
        (config.dashboard.host, config.dashboard.port), handler_factory(config_path, scanner)
    )
    print(f"Dashboard: http://{config.dashboard.host}:{config.dashboard.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
