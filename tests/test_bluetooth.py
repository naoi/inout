import unittest
from unittest.mock import patch

from inout_tracker.bluetooth import BluetoothctlScanner

OUTPUT = """
[NEW] Device AA:BB:CC:DD:EE:FF Alice iPhone
[CHG] Device AA:BB:CC:DD:EE:FF RSSI: -67
[NEW] Device 11:22:33:44:55:66 Beacon
"""


class BluetoothTests(unittest.TestCase):
    @patch.object(BluetoothctlScanner, "_scan_output", return_value=OUTPUT)
    def test_scan_matches_requested_devices(self, _scan: object) -> None:
        scanner = BluetoothctlScanner()
        self.assertEqual(
            scanner.scan(["AA:BB:CC:DD:EE:FF", "00:00:00:00:00:00"]),
            {"AA:BB:CC:DD:EE:FF": True, "00:00:00:00:00:00": False},
        )

    @patch.object(BluetoothctlScanner, "_scan_output", return_value=OUTPUT)
    def test_discover_deduplicates_change_events(self, _scan: object) -> None:
        devices = BluetoothctlScanner().discover()
        self.assertEqual(
            [(item.address, item.name) for item in devices],
            [
                ("AA:BB:CC:DD:EE:FF", "Alice iPhone"),
                ("11:22:33:44:55:66", "Beacon"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
