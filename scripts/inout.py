#!/usr/bin/env python3
"""Compatibility entry point for installations that used scripts/inout.py."""

import os
import sys

from inout_tracker.cli import main
from inout_tracker.config import DEFAULT_CONFIG_PATH

if __name__ == "__main__":
    config = os.environ.get("INOUT_CONFIG", DEFAULT_CONFIG_PATH)
    print(
        f"Deprecated entry point. Prefer: inout --config {config} run",
        file=sys.stderr,
    )
    raise SystemExit(main(["--config", config, "run", *sys.argv[1:]]))
