from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol

from .config import AppConfig, DeviceConfig
from .state import StateStore

LOG = logging.getLogger(__name__)


class Scanner(Protocol):
    def scan(self, addresses: list[str]) -> dict[str, bool]: ...


class Writer(Protocol):
    def record_presence(self, device: DeviceConfig, now: datetime) -> None: ...


@dataclass(frozen=True)
class PollResult:
    name: str
    address: str
    present: bool
    last_seen: str | None
    recorded: bool
    error: str | None = None


class AttendanceService:
    def __init__(
        self, config: AppConfig, scanner: Scanner, writer: Writer, state: StateStore
    ) -> None:
        self.config = config
        self.scanner = scanner
        self.writer = writer
        self.state = state

    def poll_once(self, now: datetime | None = None) -> list[PollResult]:
        now = now or datetime.now().astimezone()
        detected = self.scanner.scan([device.address for device in self.config.devices])
        results: list[PollResult] = []
        for device in self.config.devices:
            device_state = self.state.get(device.address)
            seen = detected.get(device.address, False)
            recorded = False
            error = None
            if seen:
                device_state.present = True
                device_state.last_seen = now.isoformat()
                try:
                    self.writer.record_presence(device, now)
                    recorded = True
                except Exception as exc:
                    error = str(exc)
                    LOG.exception("Failed to update Sheets for %s", device.name)
            elif device_state.present:
                last_seen = device_state.last_seen_datetime()
                if (
                    last_seen is None
                    or (now - last_seen).total_seconds() >= self.config.absence_grace_seconds
                ):
                    device_state.present = False
            results.append(
                PollResult(
                    device.name,
                    device.address,
                    device_state.present,
                    device_state.last_seen,
                    recorded,
                    error,
                )
            )
        self.state.save()
        return results

    @staticmethod
    def serialise(results: list[PollResult]) -> list[dict[str, object]]:
        return [asdict(result) for result in results]
