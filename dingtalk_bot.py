"""
DingTalk Bot integration module
================================
Sends text and Markdown messages to a DingTalk group robot via the outgoing
webhook URL.  Supports the optional HMAC-SHA256 "sign" security mode.

Configuration (environment variables or .env file):
    DINGTALK_WEBHOOK_URL  Required.  Full webhook URL including access_token.
    DINGTALK_SECRET       Optional.  Signing secret for added security.

Usage::

    from dingtalk_bot import DingTalkBot

    bot = DingTalkBot()          # reads from env / .env
    bot.send_text("Hello!")
    bot.send_markdown("Title", "## Hello\\nWorld")
"""

from __future__ import annotations

import hashlib
import hmac
import base64
import json
import os
import time
from typing import Any
from urllib.parse import quote, urlencode

try:
    import requests
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: requests.  Install with `pip install requests`.") from exc

# Load .env if python-dotenv is available (optional dependency)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass


class DingTalkError(RuntimeError):
    """Raised when the DingTalk API returns an error."""


class DingTalkBot:
    """Send messages to a DingTalk group robot."""

    def __init__(
        self,
        webhook_url: str | None = None,
        secret: str | None = None,
    ) -> None:
        self.webhook_url: str = (
            webhook_url
            or os.environ.get("DINGTALK_WEBHOOK_URL", "")
        ).strip()
        self.secret: str = (
            secret
            or os.environ.get("DINGTALK_SECRET", "")
        ).strip()

        if not self.webhook_url:
            raise DingTalkError(
                "DINGTALK_WEBHOOK_URL is not set.  "
                "Export it as an environment variable or add it to your .env file."
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _signed_url(self) -> str:
        """Return webhook URL with timestamp+sign appended when a secret is set."""
        if not self.secret:
            return self.webhook_url

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        sig = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = quote(base64.b64encode(sig), safe="")
        sep = "&" if "?" in self.webhook_url else "?"
        return f"{self.webhook_url}{sep}timestamp={timestamp}&sign={sign}"

    def _post(self, payload: dict[str, Any]) -> bool:
        """POST *payload* to the DingTalk webhook.  Returns True on success."""
        url = self._signed_url()
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise DingTalkError(f"Request failed: {exc}") from exc

        try:
            data = resp.json()
        except ValueError as exc:
            raise DingTalkError(f"Invalid JSON response: {resp.text}") from exc

        if data.get("errcode", 0) != 0:
            raise DingTalkError(f"DingTalk API error {data.get('errcode')}: {data.get('errmsg')}")

        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_text(self, content: str, at_mobiles: list[str] | None = None, at_all: bool = False) -> bool:
        """Send a plain-text message.

        Args:
            content:    Message body.
            at_mobiles: List of mobile numbers to @mention.
            at_all:     If True, @mentions everyone in the group.
        """
        payload: dict[str, Any] = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all,
            },
        }
        return self._post(payload)

    def send_markdown(self, title: str, text: str, at_mobiles: list[str] | None = None, at_all: bool = False) -> bool:
        """Send a Markdown message.

        Args:
            title:      Short title shown in the notification banner.
            text:       Full Markdown body.
            at_mobiles: List of mobile numbers to @mention.
            at_all:     If True, @mentions everyone in the group.
        """
        payload: dict[str, Any] = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all,
            },
        }
        return self._post(payload)
