#!/usr/bin/env python3
"""Compatibility entry point for the Bluetooth discovery command."""

from inout_tracker.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["--config", "config.example.yaml", "scan"]))
