#!/usr/bin/env python3
"""Compatibility entry point for installations that used scripts/inout.py."""

import sys

from inout_tracker.cli import main

if __name__ == "__main__":
    print(
        "Deprecated entry point. Prefer: inout --config /var/lib/inout/config.yaml run",
        file=sys.stderr,
    )
    raise SystemExit(main(["--config", "config.example.yaml", "run", *sys.argv[1:]]))
