#!/usr/bin/env python3
"""
Send a test message to DingTalk.
=================================
Reads DINGTALK_WEBHOOK_URL (and optional DINGTALK_SECRET) from the environment
or from a .env file in the repository root.

Usage::

    # 1. Copy and fill in .env.example
    cp .env.example .env
    # edit .env with your real webhook URL

    # 2. Run the test
    python scripts/send_dingtalk_message.py

    # 3. Or pass the webhook URL directly
    DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=xxx" \
        python scripts/send_dingtalk_message.py
"""

from __future__ import annotations

import datetime
import os
import sys

# Allow running from the repository root or from the scripts/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dingtalk_bot import DingTalkBot, DingTalkError


def main() -> None:
    print("🚀 Testing DingTalk integration...\n")

    try:
        bot = DingTalkBot()
    except DingTalkError as exc:
        print(f"❌ Configuration error: {exc}")
        print()
        print("Tip: set DINGTALK_WEBHOOK_URL in your environment or in a .env file.")
        print("     See .env.example for a template.")
        sys.exit(1)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- 1. text message ---
    print("1️⃣  Sending text message…")
    try:
        bot.send_text(f"✅ OpenClaw 启动成功！\n时间: {now}")
        print("   ✅ Text message sent successfully\n")
    except DingTalkError as exc:
        print(f"   ❌ Failed: {exc}\n")
        sys.exit(1)

    # --- 2. markdown message ---
    print("2️⃣  Sending Markdown message…")
    markdown_body = f"""## 📊 OpenClaw 状态报告

| 项目 | 值 |
|------|-----|
| 服务名称 | OpenClaw |
| Python 版本 | {sys.version.split()[0]} |
| 运行时间 | {now} |
| 状态 | 🟢 运行中 |

### 🎯 已启用集成
- ✅ 钉钉 (DingTalk) — 消息推送 & 通知告警
"""
    try:
        bot.send_markdown("OpenClaw 系统状态", markdown_body)
        print("   ✅ Markdown message sent successfully\n")
    except DingTalkError as exc:
        print(f"   ❌ Failed: {exc}\n")
        sys.exit(1)

    print("✨ All tests completed successfully!")


if __name__ == "__main__":
    main()
