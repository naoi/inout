import unittest

from inout_tracker.cli import parser
from inout_tracker.config import DEFAULT_CONFIG_PATH


class CliTests(unittest.TestCase):
    def test_config_defaults_to_the_installed_path(self) -> None:
        arguments = parser().parse_args(["run"])
        self.assertEqual(arguments.config, DEFAULT_CONFIG_PATH)
        self.assertEqual(DEFAULT_CONFIG_PATH, "/var/lib/inout/config.yaml")


if __name__ == "__main__":
    unittest.main()
