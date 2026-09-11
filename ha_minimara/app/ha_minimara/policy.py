from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from .errors import HAMiniMaraError

ENTITY_ID = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


@dataclass(frozen=True)
class DenPolicy:
    camera: str
    motion: str
    person: str
    animal: str
    ptz: dict[str, str]
    guard_go_to: str
    guard_return: str
    privacy_mode: str

    @classmethod
    def load(cls, path: Path) -> "DenPolicy":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if set(raw) != {"den"} or not isinstance(raw["den"], dict):
            raise HAMiniMaraError("INVALID_POLICY", "policy must contain only the den object")
        den: dict[str, Any] = raw["den"]
        expected = {
            "camera", "motion", "person", "animal", "ptz",
            "guard_go_to", "guard_return", "privacy_mode",
        }
        if set(den) != expected:
            raise HAMiniMaraError("INVALID_POLICY", "den policy keys do not match the fixed schema")
        ptz = den["ptz"]
        if not isinstance(ptz, dict) or set(ptz) != {"up", "down", "left", "right", "stop"}:
            raise HAMiniMaraError("INVALID_POLICY", "PTZ must define exactly up, down, left, right, and stop")
        values = [den[key] for key in expected if key != "ptz"] + list(ptz.values())
        if not all(isinstance(value, str) and ENTITY_ID.fullmatch(value) for value in values):
            raise HAMiniMaraError("INVALID_POLICY", "all configured values must be Home Assistant entity IDs")
        return cls(ptz=dict(ptz), **{key: den[key] for key in expected if key != "ptz"})

    @property
    def observed_entities(self) -> tuple[str, ...]:
        return (self.camera, self.motion, self.person, self.animal, self.guard_return, self.privacy_mode)

    def ptz_entity(self, direction: str) -> str:
        try:
            return self.ptz[direction]
        except KeyError:
            raise HAMiniMaraError("ACCESS_DENIED", "PTZ direction is not permitted") from None

