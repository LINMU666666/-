"""Unit tests for dingtalk_bot.py."""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

# Ensure the repo root is on the path so we can import dingtalk_bot directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dingtalk_bot  # noqa: E402  (imported after path manipulation)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sign(secret: str, timestamp: str) -> str:
    """Reproduce the HMAC-SHA256 signature DingTalk would send."""
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


# ---------------------------------------------------------------------------
# Signature verification tests
# ---------------------------------------------------------------------------

class TestVerifySignature(unittest.TestCase):

    def setUp(self):
        # Patch the module-level secret so tests are isolated.
        self._orig_secret = dingtalk_bot.DINGTALK_APP_SECRET
        dingtalk_bot.DINGTALK_APP_SECRET = "test_secret_key"

    def tearDown(self):
        dingtalk_bot.DINGTALK_APP_SECRET = self._orig_secret

    def test_valid_signature(self):
        ts = "1700000000000"
        sign = _make_sign("test_secret_key", ts)
        self.assertTrue(dingtalk_bot.verify_dingtalk_signature(ts, sign))

    def test_invalid_signature(self):
        ts = "1700000000000"
        self.assertFalse(
            dingtalk_bot.verify_dingtalk_signature(ts, "badsignature==")
        )

    def test_wrong_timestamp(self):
        ts = "1700000000000"
        sign = _make_sign("test_secret_key", "9999999999999")
        self.assertFalse(dingtalk_bot.verify_dingtalk_signature(ts, sign))

    def test_no_secret_always_passes(self):
        dingtalk_bot.DINGTALK_APP_SECRET = ""
        self.assertTrue(dingtalk_bot.verify_dingtalk_signature("ts", "anysign"))


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

class TestHelpText(unittest.TestCase):

    def test_help_contains_commands(self):
        text = dingtalk_bot.get_help_text()
        for kw in ("总结", "降AI", "改写", "帮助"):
            self.assertIn(kw, text)


# ---------------------------------------------------------------------------
# Command parsing / dispatch
# ---------------------------------------------------------------------------

class TestProcessLiteratureCommand(unittest.TestCase):

    def test_empty_returns_help(self):
        result = dingtalk_bot.process_literature_command("")
        self.assertIn("帮助", result)

    def test_mention_only_returns_help(self):
        result = dingtalk_bot.process_literature_command("@TestBot ")
        self.assertIn("帮助", result)

    def test_help_command(self):
        for cmd in ("帮助", "help", "?", "？"):
            with self.subTest(cmd=cmd):
                result = dingtalk_bot.process_literature_command(cmd)
                self.assertIn("总结", result)

    def test_summarize_no_body(self):
        result = dingtalk_bot.process_literature_command("总结")
        self.assertIn("请提供", result)

    def test_summarize_with_body_no_api_key(self):
        orig = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = ""
        try:
            result = dingtalk_bot.process_literature_command("总结 深度学习是机器学习的一个子领域。")
            self.assertIn("摘要", result)
        finally:
            dingtalk_bot.SPEEDAI_API_KEY = orig

    def test_deai_no_body(self):
        result = dingtalk_bot.process_literature_command("降AI")
        self.assertIn("请提供", result)

    def test_deai_no_api_key(self):
        orig = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = ""
        try:
            result = dingtalk_bot.process_literature_command("降AI 这是一段测试文本。")
            self.assertIn("SPEEDAI_API_KEY", result)
        finally:
            dingtalk_bot.SPEEDAI_API_KEY = orig

    def test_rewrite_no_body(self):
        result = dingtalk_bot.process_literature_command("改写")
        self.assertIn("请提供", result)

    def test_rewrite_no_api_key(self):
        orig = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = ""
        try:
            result = dingtalk_bot.process_literature_command("改写 学生是航行者。")
            self.assertIn("SPEEDAI_API_KEY", result)
        finally:
            dingtalk_bot.SPEEDAI_API_KEY = orig

    def test_unknown_command(self):
        result = dingtalk_bot.process_literature_command("未知命令 foo")
        self.assertIn("未识别", result)
        self.assertIn("帮助", result)

    def test_mention_prefix_stripped(self):
        """@mention at the start of a message should be stripped before parsing."""
        orig = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = ""
        try:
            result = dingtalk_bot.process_literature_command("@LitBot 帮助")
            self.assertIn("总结", result)
        finally:
            dingtalk_bot.SPEEDAI_API_KEY = orig

    def test_summarize_extractive_fallback(self):
        """Without API key the bot returns an extractive summary preview."""
        orig = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = ""
        text = "第一句话。第二句话。第三句话。"
        try:
            result = dingtalk_bot.summarize_literature(text)
            self.assertIn("第一句话", result)
        finally:
            dingtalk_bot.SPEEDAI_API_KEY = orig


# ---------------------------------------------------------------------------
# SpeedAI integration (mocked)
# ---------------------------------------------------------------------------

class TestSpeedAIIntegration(unittest.TestCase):

    def setUp(self):
        self._orig_key = dingtalk_bot.SPEEDAI_API_KEY
        dingtalk_bot.SPEEDAI_API_KEY = "mock_api_key"

    def tearDown(self):
        dingtalk_bot.SPEEDAI_API_KEY = self._orig_key

    def test_summarize_calls_rewrite_text(self):
        mock_module = MagicMock()
        mock_module.rewrite_text.return_value = "AI改写后的内容"
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.summarize_literature("原始文本")
        self.assertIn("AI改写后的内容", result)

    def test_deai_calls_deai_text(self):
        mock_module = MagicMock()
        mock_module.deai_text.return_value = "降AI后的内容"
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.deai_literature("原始文本")
        self.assertIn("降AI后的内容", result)

    def test_rewrite_calls_rewrite_text(self):
        mock_module = MagicMock()
        mock_module.rewrite_text.return_value = "改写后的内容"
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.rewrite_literature("原始文本")
        self.assertIn("改写后的内容", result)

    def test_summarize_handles_exception(self):
        mock_module = MagicMock()
        mock_module.rewrite_text.side_effect = RuntimeError("network error")
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.summarize_literature("原始文本")
        self.assertIn("失败", result)

    def test_deai_handles_exception(self):
        mock_module = MagicMock()
        mock_module.deai_text.side_effect = RuntimeError("network error")
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.deai_literature("原始文本")
        self.assertIn("失败", result)

    def test_rewrite_handles_exception(self):
        mock_module = MagicMock()
        mock_module.rewrite_text.side_effect = RuntimeError("network error")
        with patch.dict("sys.modules", {"speedai_client": mock_module}):
            result = dingtalk_bot.rewrite_literature("原始文本")
        self.assertIn("失败", result)


# ---------------------------------------------------------------------------
# Flask webhook endpoint tests
# ---------------------------------------------------------------------------

class TestDingTalkCallbackEndpoint(unittest.TestCase):

    def setUp(self):
        dingtalk_bot.app.config["TESTING"] = True
        self.client = dingtalk_bot.app.test_client()
        self._orig_secret = dingtalk_bot.DINGTALK_APP_SECRET
        dingtalk_bot.DINGTALK_APP_SECRET = ""  # disable sig verification by default

    def tearDown(self):
        dingtalk_bot.DINGTALK_APP_SECRET = self._orig_secret

    # ---- health check ----

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")

    # ---- text messages ----

    def test_text_message_help(self):
        payload = {
            "msgtype": "text",
            "text": {"content": "帮助"},
            "senderNick": "张三",
            "sessionWebhook": "",
        }
        with patch.object(dingtalk_bot, "send_dingtalk_reply", return_value=True) as mock_reply:
            resp = self.client.post(
                "/dingtalk/callback",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["errcode"], 0)

    def test_text_message_dispatches_reply(self):
        payload = {
            "msgtype": "text",
            "text": {"content": "帮助"},
            "senderNick": "李四",
            "sessionWebhook": "https://oapi.dingtalk.com/robot/send?access_token=abc",
        }
        with patch.object(dingtalk_bot, "send_dingtalk_reply", return_value=True) as mock_reply:
            self.client.post(
                "/dingtalk/callback",
                data=json.dumps(payload),
                content_type="application/json",
            )
            mock_reply.assert_called_once()
            call_args = mock_reply.call_args
            self.assertEqual(
                call_args[0][0],
                "https://oapi.dingtalk.com/robot/send?access_token=abc",
            )

    def test_unsupported_msgtype_sends_guidance(self):
        payload = {
            "msgtype": "image",
            "senderNick": "王五",
            "sessionWebhook": "https://oapi.dingtalk.com/robot/send?access_token=abc",
        }
        with patch.object(dingtalk_bot, "send_dingtalk_reply", return_value=True) as mock_reply:
            resp = self.client.post(
                "/dingtalk/callback",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        mock_reply.assert_called_once()

    def test_empty_body_returns_400(self):
        resp = self.client.post(
            "/dingtalk/callback",
            data="",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    # ---- signature verification ----

    def test_invalid_signature_returns_401(self):
        dingtalk_bot.DINGTALK_APP_SECRET = "real_secret"
        payload = {
            "msgtype": "text",
            "text": {"content": "帮助"},
            "sessionWebhook": "",
        }
        resp = self.client.post(
            "/dingtalk/callback",
            data=json.dumps(payload),
            content_type="application/json",
            headers={"timestamp": "1234567890000", "sign": "badsign"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_valid_signature_accepted(self):
        secret = "my_test_secret"
        dingtalk_bot.DINGTALK_APP_SECRET = secret
        ts = "1700000000000"
        sign = _make_sign(secret, ts)
        payload = {
            "msgtype": "text",
            "text": {"content": "帮助"},
            "sessionWebhook": "",
        }
        with patch.object(dingtalk_bot, "send_dingtalk_reply", return_value=True):
            resp = self.client.post(
                "/dingtalk/callback",
                data=json.dumps(payload),
                content_type="application/json",
                headers={"timestamp": ts, "sign": sign},
            )
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# send_dingtalk_reply tests (mocked HTTP)
# ---------------------------------------------------------------------------

class TestResolveWebhook(unittest.TestCase):
    """Test the SSRF-guard URL resolver."""

    def test_valid_oapi_url(self):
        url = "https://oapi.dingtalk.com/robot/send?access_token=abc"
        result = dingtalk_bot._resolve_webhook(url)
        self.assertIsNotNone(result)
        self.assertIn("oapi.dingtalk.com", result)

    def test_invalid_host_returns_none(self):
        self.assertIsNone(dingtalk_bot._resolve_webhook("https://evil.example.com/hook"))

    def test_http_scheme_returns_none(self):
        self.assertIsNone(
            dingtalk_bot._resolve_webhook("http://oapi.dingtalk.com/robot/send")
        )

    def test_empty_string_returns_none(self):
        self.assertIsNone(dingtalk_bot._resolve_webhook(""))


# ---------------------------------------------------------------------------
# send_dingtalk_reply / send_markdown_reply tests (mocked HTTP)
# ---------------------------------------------------------------------------

class TestSendDingTalkReply(unittest.TestCase):

    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}
        with patch("dingtalk_bot.requests.post", return_value=mock_resp) as mock_post:
            result = dingtalk_bot.send_dingtalk_reply(
                "https://oapi.dingtalk.com/robot/send?access_token=abc", "hello"
            )
        self.assertTrue(result)
        mock_post.assert_called_once()

    def test_failure_errcode(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 310000, "errmsg": "some error"}
        with patch("dingtalk_bot.requests.post", return_value=mock_resp):
            result = dingtalk_bot.send_dingtalk_reply(
                "https://oapi.dingtalk.com/robot/send?access_token=abc", "hello"
            )
        self.assertFalse(result)

    def test_untrusted_url_rejected(self):
        """SSRF guard: non-DingTalk URLs must be refused without an HTTP call."""
        with patch("dingtalk_bot.requests.post") as mock_post:
            result = dingtalk_bot.send_dingtalk_reply("https://evil.example.com/hook", "hi")
        self.assertFalse(result)
        mock_post.assert_not_called()

    def test_http_url_rejected(self):
        """SSRF guard: plain HTTP (non-TLS) DingTalk URLs must be refused."""
        with patch("dingtalk_bot.requests.post") as mock_post:
            result = dingtalk_bot.send_dingtalk_reply(
                "http://oapi.dingtalk.com/robot/send?access_token=abc", "hi"
            )
        self.assertFalse(result)
        mock_post.assert_not_called()

    def test_markdown_reply_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}
        with patch("dingtalk_bot.requests.post", return_value=mock_resp) as mock_post:
            result = dingtalk_bot.send_markdown_reply(
                "https://oapi.dingtalk.com/robot/send?access_token=abc", "标题", "## 内容"
            )
        self.assertTrue(result)
        call_json = mock_post.call_args[1]["json"]
        self.assertEqual(call_json["msgtype"], "markdown")

    def test_markdown_reply_untrusted_rejected(self):
        with patch("dingtalk_bot.requests.post") as mock_post:
            result = dingtalk_bot.send_markdown_reply(
                "https://attacker.com/hook", "title", "text"
            )
        self.assertFalse(result)
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
