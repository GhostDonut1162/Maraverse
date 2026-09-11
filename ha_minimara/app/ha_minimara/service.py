from __future__ import annotations

from typing import Any

from .audit import AuditLogger
from .client import HomeAssistantClient
from .policy import DenPolicy


class HAService:
    def __init__(self, client: HomeAssistantClient, policy: DenPolicy, audit: AuditLogger, actor: str) -> None:
        self.client = client
        self.policy = policy
        self.audit = audit
        self.actor = actor

    def observe(self) -> list[dict[str, Any]]:
        result = [self.client.state(entity) for entity in self.policy.observed_entities]
        self.audit.record(self.actor, "observe", "den-camera-state", "allowed")
        return result

    def snapshot(self) -> tuple[bytes, str]:
        result = self.client.snapshot(self.policy.camera)
        self.audit.record(self.actor, "snapshot", "den-camera-clear", "allowed")
        return result

    def ptz(self, direction: str) -> None:
        entity = self.policy.ptz_entity(direction)
        self.client.press(entity)
        self.audit.record(self.actor, "ptz", direction, "allowed")

    def go_to_guard(self) -> None:
        self.client.press(self.policy.guard_go_to)
        self.audit.record(self.actor, "guard_go_to", "den-camera", "allowed")

    def set_guard_return(self, enabled: bool) -> None:
        self.client.switch(self.policy.guard_return, enabled)
        self.audit.record(self.actor, "guard_return", "enabled" if enabled else "disabled", "allowed")

    def set_privacy(self, enabled: bool) -> None:
        self.client.switch(self.policy.privacy_mode, enabled)
        self.audit.record(self.actor, "privacy_mode", "enabled" if enabled else "disabled", "allowed")

