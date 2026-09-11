from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


class AuditLogger:
    def __init__(self, path: Path | None) -> None:
        self.path = path

    def record(self, actor: str, action: str, target: str, outcome: str) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
            "outcome": outcome,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, separators=(",", ":")) + "\n")

