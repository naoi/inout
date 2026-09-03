from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from .bluetooth import BluetoothctlScanner
from .config import DEFAULT_CONFIG_PATH, load_config
from .dashboard import serve_dashboard
from .errors import InOutError
from .service import AttendanceService
from .sheets import GoogleSheetsWriter
from .state import StateStore

LOG = logging.getLogger(__name__)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Bluetooth attendance logger")
    result.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="configuration YAML path")
    result.add_argument("--verbose", action="store_true")
    commands = result.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="scan and update Google Sheets")
    run.add_argument("--once", action="store_true", help="perform one poll and exit")
    commands.add_parser("scan", help="show nearby Bluetooth devices")
    commands.add_parser("check-config", help="validate config and Google Sheets access")
    commands.add_parser("dashboard", help="start the local registration dashboard")
    return result


def _service(config_path: Path) -> tuple[object, AttendanceService]:
    config = load_config(config_path)
    scanner = BluetoothctlScanner(config.bluetooth_scan_seconds)
    writer = GoogleSheetsWriter(config.google.credentials_file)
    state = StateStore(config.state_file)
    return config, AttendanceService(config, scanner, writer, state)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config_path = Path(args.config).expanduser().resolve()
    try:
        if args.command == "dashboard":
            serve_dashboard(config_path)
            return 0
        config, service = _service(config_path)
        if args.command == "scan":
            scanner = BluetoothctlScanner(config.bluetooth_scan_seconds)
            print(json.dumps([item.__dict__ for item in scanner.discover()], indent=2))
            return 0
        if args.command == "check-config":
            writer = GoogleSheetsWriter(config.google.credentials_file)
            for device in config.devices:
                writer.check_access(device)
                print(f"OK: {device.name}: {device.spreadsheet_id}")
            return 0
        if args.command == "run":
            failures = 0
            while True:
                try:
                    results = service.poll_once()
                    print(json.dumps(service.serialise(results), ensure_ascii=False))
                    failures = 0
                except InOutError as exc:
                    failures += 1
                    delay = min(300, 2**failures)
                    LOG.error("Poll failed: %s; retry in %s seconds", exc, delay)
                    if args.once:
                        raise
                    time.sleep(delay)
                    continue
                if args.once:
                    return 1 if any(item.error for item in results) else 0
                time.sleep(config.polling_interval_seconds)
    except (InOutError, OSError) as exc:
        LOG.error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
