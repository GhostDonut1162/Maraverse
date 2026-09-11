from __future__ import annotations

import base64
import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ImageContent, TextContent, Tool

from .audit import AuditLogger
from .client import HomeAssistantClient
from .errors import HAMiniMaraError
from .policy import DenPolicy
from .service import HAService

ACTOR = "chat-mara-ha-den-camera"
TOOL_NAMES = frozenset({
    "ha_den_observe", "ha_den_snapshot", "ha_den_ptz",
    "ha_den_guard_go_to", "ha_den_guard_return", "ha_den_privacy_mode",
})


class StrictMCPServer(MCPServer):
    """Advertise the SDK's strict function-call argument boundary."""

    async def list_tools(self) -> list[Tool]:
        tools = await super().list_tools()
        for tool in tools:
            tool.input_schema["additionalProperties"] = False
        return tools


def _build_service() -> HAService:
    policy_path = Path(os.environ.get("HA_MINIMARA_POLICY", "config/policy.json"))
    audit_value = os.environ.get("HA_MINIMARA_AUDIT")
    token = os.environ.get("HA_MINIMARA_TOKEN") or os.environ.get("SUPERVISOR_TOKEN", "")
    base_url = os.environ.get("HA_MINIMARA_URL", "")
    return HAService(
        HomeAssistantClient(base_url, token),
        DenPolicy.load(policy_path),
        AuditLogger(Path(audit_value) if audit_value else None),
        ACTOR,
    )


def _call(action):
    try:
        return action()
    except HAMiniMaraError as exc:
        raise ToolError(f"{exc.code}: {exc}") from None


def create_server(service: HAService | None = None) -> MCPServer:
    ha = service or _build_service()
    server = StrictMCPServer(
        name="ha-minimara-den",
        title="HA MiniMara Den Camera",
        description="Least-privilege Home Assistant access limited to the Den Reolink E1 Pro.",
        instructions=(
            "Home Assistant access is limited to the Den camera. Observe by default. "
            "PTZ, guard return, and privacy tools cause physical or privacy changes and require explicit user intent."
        ),
        version="0.1.0",
    )

    @server.tool(name="ha_den_observe")
    def observe() -> list[dict]:
        """Read current Den camera, motion, person, animal, guard-return, and privacy states."""
        return _call(ha.observe)

    @server.tool(name="ha_den_snapshot")
    def snapshot() -> list[ImageContent | TextContent]:
        """Fetch one transient high-resolution still from the approved Clear camera entity."""
        data, mime = _call(ha.snapshot)
        return [ImageContent(type="image", data=base64.b64encode(data).decode("ascii"), mimeType=mime)]

    @server.tool(name="ha_den_ptz")
    def ptz(direction: str) -> str:
        """Press one approved PTZ direction: up, down, left, right, or stop."""
        _call(lambda: ha.ptz(direction))
        return "PTZ command accepted"

    @server.tool(name="ha_den_guard_go_to")
    def guard_go_to() -> str:
        """Return the Den camera to its configured guard position."""
        _call(ha.go_to_guard)
        return "Guard-position command accepted"

    @server.tool(name="ha_den_guard_return")
    def guard_return(enabled: bool) -> str:
        """Enable or disable the approved Den camera guard-return switch."""
        _call(lambda: ha.set_guard_return(enabled))
        return "Guard-return setting accepted"

    @server.tool(name="ha_den_privacy_mode")
    def privacy_mode(enabled: bool) -> str:
        """Enable or disable Den camera privacy mode."""
        _call(lambda: ha.set_privacy(enabled))
        return "Privacy-mode setting accepted"

    return server


def main() -> None:
    create_server().run("stdio")
