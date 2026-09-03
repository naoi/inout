import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from inout_tracker.config import AppConfig, DashboardConfig, DeviceConfig, GoogleConfig
from inout_tracker.service import AttendanceService
from inout_tracker.state import StateStore


class Scanner:
    def __init__(self, present: bool) -> None:
        self.present = present

    def scan(self, addresses: list[str]) -> dict[str, bool]:
        return {address: self.present for address in addresses}


class Writer:
    def __init__(self) -> None:
        self.calls = []

    def record_presence(self, device: DeviceConfig, now: datetime) -> None:
        self.calls.append((device, now))


def make_config(root: Path) -> AppConfig:
    return AppConfig(
        devices=(DeviceConfig("Alice", "AA:BB:CC:DD:EE:FF", "12345678901234567890"),),
        google=GoogleConfig(root / "credentials.json"),
        dashboard=DashboardConfig(),
        absence_grace_seconds=120,
        state_file=root / "state.json",
    )


class ServiceTests(unittest.TestCase):
    def test_presence_is_recorded_and_absence_uses_grace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            app_config = make_config(Path(directory))
            state = StateStore(app_config.state_file)
            writer = Writer()
            scanner = Scanner(True)
            service = AttendanceService(app_config, scanner, writer, state)
            start = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)

            first = service.poll_once(start)
            self.assertTrue(first[0].present)
            self.assertTrue(first[0].recorded)
            self.assertEqual(len(writer.calls), 1)

            scanner.present = False
            within_grace = service.poll_once(start + timedelta(seconds=60))
            self.assertTrue(within_grace[0].present)

            absent = service.poll_once(start + timedelta(seconds=121))
            self.assertFalse(absent[0].present)


if __name__ == "__main__":
    unittest.main()
