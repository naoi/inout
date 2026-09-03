import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inout_tracker.config import ConfigurationError, DeviceConfig, add_device, load_config


def write_config(path: Path, extra: str = "") -> None:
    path.write_text(
        """version: 1
google:
  credentials_file: credentials.json
state_file: state.json
devices:
  - name: Alice
    address: AA:BB:CC:DD:EE:FF
    spreadsheet_id: "12345678901234567890"
"""
        + extra,
        encoding="utf-8",
    )


class ConfigTests(unittest.TestCase):
    def test_loads_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_file = root / "config.yaml"
            write_config(config_file)
            config = load_config(config_file)
            self.assertEqual(config.google.credentials_file, (root / "credentials.json").resolve())
            self.assertEqual(config.state_file, (root / "state.json").resolve())
            self.assertEqual(config.devices[0].address, "AA:BB:CC:DD:EE:FF")

    def test_rejects_invalid_address(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            write_config(config_file)
            config_file.write_text(config_file.read_text().replace("AA:BB:CC:DD:EE:FF", "phone"))
            with self.assertRaisesRegex(ConfigurationError, "address"):
                load_config(config_file)

    def test_requires_token_for_lan_bind(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            config_file = Path(directory) / "config.yaml"
            write_config(config_file, "dashboard:\n  host: 0.0.0.0\n")
            with self.assertRaisesRegex(ConfigurationError, "token"):
                load_config(config_file)

    def test_add_device_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            write_config(config_file)
            add_device(
                config_file,
                DeviceConfig("Bob", "11:22:33:44:55:66", "abcdefghijklmnopqrst", 123),
            )
            config = load_config(config_file)
            self.assertEqual([item.name for item in config.devices], ["Alice", "Bob"])
            self.assertEqual(config.devices[1].template_sheet_id, 123)


if __name__ == "__main__":
    unittest.main()
