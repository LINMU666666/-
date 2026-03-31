"""
DingTalk Bot for "Read Literature" Workflow
============================================
Webhook server that receives DingTalk messages, parses literature commands,
integrates with SpeedAI, and replies with results.

Supported commands (send inside a DingTalk group/chat after @-mentioning the bot):
  总结 <text>   – Generate a summary / rewrite of the given passage
  降AI <text>   – Reduce AI-detection score of the passage
  改写 <text>   – Rewrite the passage
  帮助 / help   – Show the help text

Environment variables (all optional unless noted):
  DINGTALK_APP_SECRET   – App secret for verifying incoming request signatures
  SPEEDAI_API_KEY       – SpeedAI API key; without it only stub responses are returned
  PORT                  – HTTP port to listen on (default: 8080)

Usage:
  pip install -r requirements.txt
  export DINGTALK_APP_SECRET="<your-app-secret>"
  export SPEEDAI_API_KEY="<your-speedai-key>"
  python dingtalk_bot.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DINGTALK_APP_SECRET: str = os.getenv("DINGTALK_APP_SECRET", "")
SPEEDAI_API_KEY: str = os.getenv("SPEEDAI_API_KEY", "")

# Allowed hostnames for outbound DingTalk sessionWebhook calls (SSRF guard).
_ALLOWED_WEBHOOK_HOSTS: frozenset[str] = frozenset(
    {
        "oapi.dingtalk.com",
        "oapi.dingtalk.com.cn",
    }
)


def _resolve_webhook(session_webhook: str) -> str | None:
    """Validate *session_webhook* and return a safe URL, or ``None`` if untrusted.

    The host is resolved from *_ALLOWED_WEBHOOK_HOSTS* (a trusted constant set)
    rather than from the user-supplied string, so the outbound host cannot be
    attacker-controlled even if the incoming request body is tampered with.
    """
    try:
        parsed = urlparse(session_webhook)
    except Exception:
        return None
    if parsed.scheme != "https":
        return None
    # Resolve the host from our trusted allowlist, not from user input.
    matched_host: str | None = None
    for allowed in _ALLOWED_WEBHOOK_HOSTS:
        if parsed.hostname == allowed:
            matched_host = allowed
            break
    if matched_host is None:
        return None
    path = parsed.path or "/robot/send"
    qs = ("?" + parsed.query) if parsed.query else ""
    return f"https://{matched_host}{path}{qs}"

# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def verify_dingtalk_signature(timestamp: str, sign: str) -> bool:
    """Return True when the DingTalk HMAC-SHA256 signature is valid.

    DingTalk passes 'timestamp' and 'sign' as HTTP headers.
    The signature is: base64(HMAC-SHA256(timestamp + "\\n" + app_secret)).
    Signature verification is skipped when DINGTALK_APP_SECRET is not set.
    """
    if not DINGTALK_APP_SECRET:
        return True  # verification disabled in development

    string_to_sign = f"{timestamp}\n{DINGTALK_APP_SECRET}"
    computed = hmac.new(
        DINGTALK_APP_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    expected = base64.b64encode(computed).decode("utf-8")
    return hmac.compare_digest(expected, sign)


# ---------------------------------------------------------------------------
# DingTalk reply helpers
# ---------------------------------------------------------------------------

def send_dingtalk_reply(session_webhook: str, content: str) -> bool:
    """Send a plain-text reply to a DingTalk conversation.

    DingTalk provides a *sessionWebhook* URL in each incoming message that
    is valid for a short window (10 minutes).  POST a message object to it.
    Only HTTPS URLs on known DingTalk hostnames are accepted (SSRF guard).
    """
    safe_url = _resolve_webhook(session_webhook)
    if safe_url is None:
        logger.error("Untrusted sessionWebhook URL rejected: %s", session_webhook)
        return False
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        resp = requests.post(safe_url, json=payload, timeout=10)
        result = resp.json()
        if result.get("errcode") == 0:
            return True
        logger.error("DingTalk reply failed: %s", result)
        return False
    except Exception as exc:  # pragma: no cover
        logger.error("DingTalk reply error: %s", exc)
        return False


def send_markdown_reply(session_webhook: str, title: str, text: str) -> bool:
    """Send a Markdown reply to a DingTalk conversation.

    Only HTTPS URLs on known DingTalk hostnames are accepted (SSRF guard).
    """
    safe_url = _resolve_webhook(session_webhook)
    if safe_url is None:
        logger.error("Untrusted sessionWebhook URL rejected: %s", session_webhook)
        return False
    payload = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
    try:
        resp = requests.post(safe_url, json=payload, timeout=10)
        result = resp.json()
        if result.get("errcode") == 0:
            return True
        logger.error("DingTalk markdown reply failed: %s", result)
        return False
    except Exception as exc:  # pragma: no cover
        logger.error("DingTalk markdown reply error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Command processing
# ---------------------------------------------------------------------------

# Regex to strip leading @<name> mentions from a message
_MENTION_RE = re.compile(r"^@\S+\s*")


def _strip_mention(content: str) -> str:
    """Remove a leading @mention from *content*."""
    return _MENTION_RE.sub("", content).strip()


def _split_command(content: str) -> tuple[str, str]:
    """Return (command_keyword, body) from a space-delimited message."""
    parts = content.split(None, 1)
    cmd = parts[0].lower() if parts else ""
    body = parts[1].strip() if len(parts) > 1 else ""
    return cmd, body


def get_help_text() -> str:
    """Return the bot's help/usage text."""
    return (
        "📚 文献阅读助手 - 使用说明\n\n"
        "支持的命令：\n"
        "  总结 <文本>   – 生成文献摘要\n"
        "  降AI <文本>   – 降低AI痕迹\n"
        "  改写 <文本>   – 改写文献段落\n"
        "  帮助 / help  – 显示此帮助\n\n"
        "示例：\n"
        "  总结 近年来，深度学习在自然语言处理领域取得了重大进展…\n"
        "  降AI 本研究旨在探讨…\n"
        "  改写 学生是知识海洋中的航行者…"
    )


def summarize_literature(text: str) -> str:
    """Summarize *text* via SpeedAI rewrite, or fall back to sentence extraction."""
    if not SPEEDAI_API_KEY:
        sentences = [s.strip() for s in re.split(r"[。！？\n]", text) if s.strip()]
        preview = "。".join(sentences[:2]) + ("。" if sentences else "")
        return (
            f"📄 摘要（提取式）：\n{preview or text[:200]}\n\n"
            "（提示：设置 SPEEDAI_API_KEY 以启用 AI 摘要）"
        )

    try:
        from speedai_client import rewrite_text  # local import avoids hard dependency

        result = rewrite_text(
            apikey=SPEEDAI_API_KEY,
            text=text,
            lang="Chinese",
            rewrite_type="weipu",  # 维普 – Chinese academic database style
        )
        return f"📄 文献摘要：\n{result}"
    except Exception as exc:
        logger.error("SpeedAI summarize error: %s", exc)
        return f"📄 摘要生成失败：{exc}\n请检查 SPEEDAI_API_KEY 配置。"


def deai_literature(text: str) -> str:
    """Reduce AI-detection score of *text* using SpeedAI."""
    if not SPEEDAI_API_KEY:
        return (
            "⚠️ 未配置 SPEEDAI_API_KEY，无法执行降AI操作。\n"
            f"原文（前200字）：\n{text[:200]}"
        )

    try:
        from speedai_client import deai_text

        result = deai_text(
            apikey=SPEEDAI_API_KEY,
            text=text,
            lang="Chinese",
            deai_type="weipu",  # 维普 – Chinese academic database style
        )
        return f"✅ 降AI结果：\n{result}"
    except Exception as exc:
        logger.error("SpeedAI deai error: %s", exc)
        return f"降AI处理失败：{exc}"


def rewrite_literature(text: str) -> str:
    """Rewrite *text* using SpeedAI."""
    if not SPEEDAI_API_KEY:
        return (
            "⚠️ 未配置 SPEEDAI_API_KEY，无法执行改写操作。\n"
            f"原文（前200字）：\n{text[:200]}"
        )

    try:
        from speedai_client import rewrite_text

        result = rewrite_text(
            apikey=SPEEDAI_API_KEY,
            text=text,
            lang="Chinese",
            rewrite_type="weipu",  # 维普 – Chinese academic database style
        )
        return f"✅ 改写结果：\n{result}"
    except Exception as exc:
        logger.error("SpeedAI rewrite error: %s", exc)
        return f"改写处理失败：{exc}"


def process_literature_command(raw_content: str) -> str:
    """Parse *raw_content* and dispatch to the appropriate handler.

    Returns a plain-text reply string.
    """
    content = _strip_mention(raw_content)

    if not content:
        return get_help_text()

    cmd, body = _split_command(content)

    if cmd in ("帮助", "help", "?", "？"):
        return get_help_text()

    if cmd in ("总结", "summary", "summarize"):
        if not body:
            return "请提供要总结的文献内容，例如：总结 [文献摘要内容]"
        return summarize_literature(body)

    if cmd in ("降ai", "deai", "去ai"):
        if not body:
            return "请提供要处理的文本，例如：降AI [文本内容]"
        return deai_literature(body)

    if cmd in ("改写", "rewrite"):
        if not body:
            return "请提供要改写的文本，例如：改写 [文本内容]"
        return rewrite_literature(body)

    return f"未识别的命令：{content[:50]!r}\n\n{get_help_text()}"


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/dingtalk/callback", methods=["POST"])
def dingtalk_callback():
    """Receive and process incoming DingTalk bot messages.

    DingTalk delivers a JSON body for every message that @-mentions the bot.
    The handler verifies the request signature, dispatches the command, and
    sends a reply via the *sessionWebhook* URL embedded in the request.
    """
    timestamp = request.headers.get("timestamp", "")
    sign = request.headers.get("sign", "")

    if timestamp and sign and not verify_dingtalk_signature(timestamp, sign):
        logger.warning("Invalid DingTalk signature from %s", request.remote_addr)
        return jsonify({"errcode": 401, "errmsg": "Invalid signature"}), 401

    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"errcode": 400, "errmsg": "Empty or invalid JSON body"}), 400

    msg_type = body.get("msgtype", "")
    session_webhook = body.get("sessionWebhook", "")
    sender_nick = body.get("senderNick", "用户")

    if msg_type == "text":
        raw_content = body.get("text", {}).get("content", "").strip()
        logger.info("Message from %s: %.80s", sender_nick, raw_content)

        reply = process_literature_command(raw_content)

        if session_webhook:
            send_dingtalk_reply(session_webhook, reply)

        return jsonify({"errcode": 0, "errmsg": "ok"})

    # Unsupported message type
    if session_webhook:
        send_dingtalk_reply(
            session_webhook,
            "📚 文献助手仅支持文本消息，请发送文字命令。\n发送「帮助」查看支持的命令。",
        )
    return jsonify({"errcode": 0, "errmsg": "ok"})


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness probe."""
    return jsonify({"status": "ok", "service": "dingtalk-literature-bot"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    port = int(os.getenv("PORT", "8080"))
    logger.info("Starting DingTalk Literature Bot on port %d", port)
    app.run(host="0.0.0.0", port=port)
