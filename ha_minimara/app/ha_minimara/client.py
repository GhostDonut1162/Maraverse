from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .errors import HAMiniMaraError


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        secure_external = base_url.startswith("https://")
        protected_app_proxy = base_url.rstrip("/") == "http://supervisor/core"
        if not (secure_external or protected_app_proxy):
            raise HAMiniMaraError(
                "INVALID_CONFIG",
                "Home Assistant URL must use HTTPS or the protected App Core API proxy",
            )
        if not token:
            raise HAMiniMaraError("MISSING_SECRET", "Home Assistant token is unavailable")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(self, path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[bytes, str]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout, context=ssl.create_default_context()) as response:
                return response.read(), response.headers.get_content_type()
        except HTTPError as exc:
            raise HAMiniMaraError("UPSTREAM_ERROR", f"Home Assistant returned HTTP {exc.code}") from None
        except URLError:
            raise HAMiniMaraError("UPSTREAM_UNAVAILABLE", "Home Assistant is unavailable") from None

    def state(self, entity_id: str) -> dict[str, Any]:
        raw, _ = self._request(f"/api/states/{quote(entity_id, safe='._')}")
        value = json.loads(raw)
        return {"entity_id": value["entity_id"], "state": value["state"], "last_updated": value.get("last_updated")}

    def snapshot(self, entity_id: str) -> tuple[bytes, str]:
        return self._request(f"/api/camera_proxy/{quote(entity_id, safe='._')}")

    def press(self, entity_id: str) -> None:
        self._request("/api/services/button/press", "POST", {"entity_id": entity_id})

    def switch(self, entity_id: str, enabled: bool) -> None:
        service = "turn_on" if enabled else "turn_off"
        self._request(f"/api/services/switch/{service}", "POST", {"entity_id": entity_id})
