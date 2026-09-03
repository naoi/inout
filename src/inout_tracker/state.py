from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class DeviceState:
    present: bool = False
    last_seen: str | None = None

    def last_seen_datetime(self) -> datetime | None:
        return datetime.fromisoformat(self.last_seen) if self.last_seen else None


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.states = self._load()

    def _load(self) -> dict[str, DeviceState]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return {
                address: DeviceState(bool(value.get("present")), value.get("last_seen"))
                for address, value in raw.items()
                if isinstance(value, dict)
            }
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, TypeError):
            return {}

    def get(self, address: str) -> DeviceState:
        return self.states.setdefault(address, DeviceState())

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {address: asdict(state) for address, state in self.states.items()},
            indent=2,
            sort_keys=True,
        )
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.path.parent, delete=False
        ) as handle:
            handle.write(payload + "\n")
            temporary = Path(handle.name)
        os.replace(temporary, self.path)
