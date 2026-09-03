from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass

from .errors import BluetoothError

DEVICE_RE = re.compile(r"\bDevice\s+([0-9A-F]{2}(?::[0-9A-F]{2}){5})(?:\s+(.+))?", re.IGNORECASE)


@dataclass(frozen=True)
class DiscoveredDevice:
    address: str
    name: str


class BluetoothctlScanner:
    def __init__(self, scan_seconds: int = 8) -> None:
        self.scan_seconds = scan_seconds

    def _scan_output(self) -> str:
        if not shutil.which("bluetoothctl"):
            raise BluetoothError("bluetoothctl was not found; install the BlueZ package")
        try:
            result = subprocess.run(
                ["bluetoothctl", "--timeout", str(self.scan_seconds), "scan", "on"],
                capture_output=True,
                text=True,
                timeout=self.scan_seconds + 5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BluetoothError(f"Bluetooth scan failed: {exc}") from exc
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode not in (0, 124) and "Discovery started" not in output:
            detail = output.strip().splitlines()[-1] if output.strip() else "unknown BlueZ error"
            raise BluetoothError(f"bluetoothctl failed: {detail}")
        return output

    def discover(self) -> list[DiscoveredDevice]:
        found: dict[str, DiscoveredDevice] = {}
        for match in DEVICE_RE.finditer(self._scan_output()):
            address = match.group(1).upper()
            name = (match.group(2) or "Unknown device").strip()
            if name.startswith(("RSSI:", "ManufacturerData")):
                name = found.get(address, DiscoveredDevice(address, "Unknown device")).name
            found[address] = DiscoveredDevice(address, name)
        return sorted(found.values(), key=lambda item: (item.name.lower(), item.address))

    def scan(self, addresses: list[str]) -> dict[str, bool]:
        requested = {address.upper() for address in addresses}
        seen = {match.group(1).upper() for match in DEVICE_RE.finditer(self._scan_output())}
        return {address: address in seen for address in requested}
