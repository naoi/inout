#!/usr/bin/env python3
"""Compatibility entry point for the Bluetooth discovery command."""

import os

from inout_tracker.cli import main
from inout_tracker.config import DEFAULT_CONFIG_PATH

if __name__ == "__main__":
    config = os.environ.get("INOUT_CONFIG", DEFAULT_CONFIG_PATH)
    raise SystemExit(main(["--config", config, "scan"]))
