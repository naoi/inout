from __future__ import annotations

import io
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError as RoundTripError

from .errors import ConfigurationError

DEFAULT_CONFIG_PATH = "/var/lib/inout/config.yaml"

ADDRESS_RE = re.compile(r"^[0-9A-F]{2}(?::[0-9A-F]{2}){5}$")
SHEET_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
UNEXPANDED_ENV_RE = re.compile(r"\$\{[^}]+\}")
SEQUENCE_ITEM_RE = re.compile(r"^(\s*)-\s")


@dataclass(frozen=True)
class DeviceConfig:
    name: str
    address: str
    spreadsheet_id: str
    template_sheet_id: int | None = None


@dataclass(frozen=True)
class GoogleConfig:
    credentials_file: Path


@dataclass(frozen=True)
class DashboardConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    token_env: str = "INOUT_DASHBOARD_TOKEN"


@dataclass(frozen=True)
class AppConfig:
    devices: tuple[DeviceConfig, ...]
    google: GoogleConfig
    dashboard: DashboardConfig
    polling_interval_seconds: int = 20
    absence_grace_seconds: int = 120
    bluetooth_scan_seconds: int = 8
    state_file: Path = Path("/var/lib/inout/state.json")


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field: str, minimum: int = 1, maximum: int = 86400) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ConfigurationError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def _parse_device(raw: Any, index: int) -> DeviceConfig:
    if not isinstance(raw, dict):
        raise ConfigurationError(f"devices[{index}] must be a mapping")
    name = _required_string(raw.get("name"), f"devices[{index}].name")
    address = _required_string(raw.get("address"), f"devices[{index}].address").upper()
    if not ADDRESS_RE.fullmatch(address):
        raise ConfigurationError(f"devices[{index}].address must look like AA:BB:CC:DD:EE:FF")
    spreadsheet_id = _required_string(raw.get("spreadsheet_id"), f"devices[{index}].spreadsheet_id")
    if not SHEET_ID_RE.fullmatch(spreadsheet_id):
        raise ConfigurationError(f"devices[{index}].spreadsheet_id is not a valid Sheets id")
    source = raw.get("template_sheet_id")
    if source is not None:
        source = _positive_int(source, f"devices[{index}].template_sheet_id", 0, 2147483647)
    return DeviceConfig(name, address, spreadsheet_id, source)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser().resolve()
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"cannot read config file {config_path}: {exc}") from exc

    expanded = os.path.expandvars(text)
    missing = sorted(set(UNEXPANDED_ENV_RE.findall(expanded)))
    if missing:
        raise ConfigurationError(f"unresolved environment variables: {', '.join(missing)}")
    try:
        raw = yaml.safe_load(expanded)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be a mapping")

    raw_devices = raw.get("devices")
    if not isinstance(raw_devices, list) or not raw_devices:
        raise ConfigurationError("devices must contain at least one device")
    devices = tuple(_parse_device(item, index) for index, item in enumerate(raw_devices))
    addresses = [device.address for device in devices]
    if len(set(addresses)) != len(addresses):
        raise ConfigurationError("device addresses must be unique")

    google = raw.get("google") or {}
    if not isinstance(google, dict):
        raise ConfigurationError("google must be a mapping")
    credentials = Path(
        _required_string(google.get("credentials_file"), "google.credentials_file")
    ).expanduser()
    if not credentials.is_absolute():
        credentials = config_path.parent / credentials

    dashboard_raw = raw.get("dashboard") or {}
    if not isinstance(dashboard_raw, dict):
        raise ConfigurationError("dashboard must be a mapping")
    dashboard = DashboardConfig(
        host=str(dashboard_raw.get("host", "127.0.0.1")),
        port=_positive_int(dashboard_raw.get("port", 8080), "dashboard.port", 1, 65535),
        token_env=str(dashboard_raw.get("token_env", "INOUT_DASHBOARD_TOKEN")),
    )
    if dashboard.host not in {"127.0.0.1", "localhost", "::1"} and not os.getenv(
        dashboard.token_env
    ):
        raise ConfigurationError(
            f"dashboard.token_env ({dashboard.token_env}) must be set when binding outside localhost"
        )

    state_file = Path(raw.get("state_file", "/var/lib/inout/state.json")).expanduser()
    if not state_file.is_absolute():
        state_file = config_path.parent / state_file

    return AppConfig(
        devices=devices,
        google=GoogleConfig(credentials.resolve()),
        dashboard=dashboard,
        polling_interval_seconds=_positive_int(
            raw.get("polling_interval_seconds", 20), "polling_interval_seconds", 5, 3600
        ),
        absence_grace_seconds=_positive_int(
            raw.get("absence_grace_seconds", 120), "absence_grace_seconds", 5, 86400
        ),
        bluetooth_scan_seconds=_positive_int(
            raw.get("bluetooth_scan_seconds", 8), "bluetooth_scan_seconds", 2, 60
        ),
        state_file=state_file.resolve(),
    )


def _sequence_offset(text: str, key: str) -> int:
    """Return the indentation the existing items of a top-level sequence use."""
    inside = False
    for line in text.splitlines():
        if not inside:
            inside = line.rstrip() == f"{key}:"
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = SEQUENCE_ITEM_RE.match(line)
        return len(match.group(1)) if match else 2
    return 2


def add_device(path: str | Path, device: DeviceConfig) -> None:
    """Append a validated device using an atomic same-directory replacement.

    The file is edited in round-trip mode so that comments, blank lines and the
    indentation an operator wrote by hand survive a dashboard registration.
    """
    config_path = Path(path).expanduser().resolve()
    editor = YAML()
    editor.preserve_quotes = True
    try:
        text = config_path.read_text(encoding="utf-8")
        offset = _sequence_offset(text, "devices")
        editor.indent(mapping=2, sequence=offset + 2, offset=offset)
        raw = editor.load(text)
    except (OSError, RoundTripError) as exc:
        raise ConfigurationError(f"cannot update config file {config_path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("devices"), list):
        raise ConfigurationError("configuration must have a devices list")
    _parse_device(
        {
            "name": device.name,
            "address": device.address,
            "spreadsheet_id": device.spreadsheet_id,
            "template_sheet_id": device.template_sheet_id,
        },
        len(raw["devices"]),
    )
    if any(str(item.get("address", "")).upper() == device.address for item in raw["devices"]):
        raise ConfigurationError(f"device {device.address} is already registered")
    entry: dict[str, Any] = {
        "name": device.name,
        "address": device.address,
        "spreadsheet_id": device.spreadsheet_id,
    }
    if device.template_sheet_id is not None:
        entry["template_sheet_id"] = device.template_sheet_id
    raw["devices"].append(entry)
    buffer = io.StringIO()
    editor.dump(raw, buffer)
    rendered = buffer.getvalue()
    mode = config_path.stat().st_mode & 0o777
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=config_path.parent, delete=False
        ) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        temporary.chmod(mode)
        os.replace(temporary, config_path)
    except OSError as exc:
        raise ConfigurationError(f"cannot write config file {config_path}: {exc}") from exc
