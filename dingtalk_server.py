"""
DingTalk Incoming Webhook Server
=================================
Listens for messages forwarded from DingTalk (outgoing messages / callbacks)
and replies automatically.

Run::

    python dingtalk_server.py           # default port 8080
    python dingtalk_server.py --port 9000

DingTalk outgoing robot (企业内部机器人 → 消息接收地址) should point to::

    http://<your-server>:<port>/dingtalk/callback

The handler validates the optional DingTalk request signature
(X-DingTalk-Signature header) and replies with a text message via
the group robot webhook (DINGTALK_WEBHOOK_URL).

Configuration (environment variables or .env):
    DINGTALK_WEBHOOK_URL  Required.  Outgoing robot webhook.
    DINGTALK_SECRET       Optional.  Signing secret for outgoing robot.
    DINGTALK_APP_SECRET   Optional.  App-level secret to validate incoming
                                     requests from DingTalk.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

from dingtalk_bot import DingTalkBot, DingTalkError

_APP_SECRET: str = os.environ.get("DINGTALK_APP_SECRET", "").strip()


def _verify_signature(body: bytes, timestamp: str, received_sign: str) -> bool:
    """Verify the X-DingTalk-Signature header sent by DingTalk."""
    if not _APP_SECRET:
        return True  # signature verification disabled

    string_to_sign = f"{timestamp}\n{_APP_SECRET}"
    expected = base64.b64encode(
        hmac.new(
            _APP_SECRET.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    return expected == received_sign


def _handle_message(payload: dict[str, Any]) -> str | None:
    """Process an incoming DingTalk message; return a reply string or None."""
    msg_type = payload.get("msgtype", "")
    text: str = ""

    if msg_type == "text":
        text = (payload.get("text") or {}).get("content", "").strip()
    else:
        # For other message types just acknowledge
        return "✅ Message received (non-text message types are acknowledged but not processed)"

    if not text:
        return None

    # --- simple reply logic ---------------------------------------------------
    text_lower = text.lower()

    if any(kw in text_lower for kw in ("help", "帮助", "?", "？")):
        return (
            "🤖 **OpenClaw Bot** 可用命令:\n"
            "- `status` — 查看系统状态\n"
            "- `help`   — 显示此帮助信息"
        )

    if any(kw in text_lower for kw in ("status", "状态", "ping")):
        import datetime
        return (
            f"✅ OpenClaw 运行正常\n"
            f"⏰ 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # Default echo reply
    return f"收到消息: {text}"


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for DingTalk callbacks."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        print(f"[dingtalk_server] {format % args}")

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/health"):
            self._send_json(200, {"status": "ok", "service": "dingtalk_server"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/dingtalk/callback":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        # Optional signature validation
        timestamp = self.headers.get("timestamp", "")
        received_sign = self.headers.get("sign", "")
        if timestamp and received_sign:
            if not _verify_signature(body, timestamp, received_sign):
                self._send_json(403, {"error": "signature mismatch"})
                return

        try:
            payload: dict[str, Any] = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "invalid JSON"})
            return

        reply = _handle_message(payload)
        if reply:
            try:
                bot = DingTalkBot()
                bot.send_text(reply)
                print(f"[dingtalk_server] Reply sent: {reply[:80]}")
            except DingTalkError as exc:
                print(f"[dingtalk_server] Failed to send reply: {exc}")

        # DingTalk expects HTTP 200 with a JSON body
        self._send_json(200, {"errcode": 0, "errmsg": "ok"})


def run(port: int = 8080) -> None:
    server = HTTPServer(("0.0.0.0", port), _Handler)
    print(f"[dingtalk_server] Listening on http://0.0.0.0:{port}")
    print(f"[dingtalk_server] Callback endpoint: http://0.0.0.0:{port}/dingtalk/callback")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[dingtalk_server] Shutting down.")
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="DingTalk incoming webhook server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()
    run(port=args.port)


if __name__ == "__main__":
    main()
