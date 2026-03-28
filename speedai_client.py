"""
SpeedAI API client sample (sync + async)
========================================
This script fixes and hardens the provided sample so it runs cleanly:
  - Correct WebSocket URL query encoding (no HTML entities)
  - Safe asyncio usage via asyncio.run()
  - Clear error handling and timeouts
  - Configurable API key, mode, type, and file path via CLI / env
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

try:
    import requests
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing dependency: requests. Install with `pip install requests`.") from exc

try:
    import websockets
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing dependency: websockets. Install with `pip install websockets`.") from exc

API_BASE = "https://api.speedai.vip"
WS_BASE = "wss://api.speedai.vip"
AISURVEY_WS_BASE = "wss://api3.speedai.chat"


class SpeedAIError(RuntimeError):
    pass


def _bi(en: str, cn: str) -> str:
    """Format bilingual message consistently: English first, Chinese in parentheses."""
    return f"{en} ({cn})"


def _post_json(url: str, payload: dict, *, timeout: int = 30) -> dict:
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise SpeedAIError(f"Request failed: {exc}") from exc

    if resp.status_code != 200:
        raise SpeedAIError(f"HTTP {resp.status_code}: {resp.text}")

    try:
        return resp.json()
    except ValueError as exc:
        raise SpeedAIError(f"Invalid JSON response: {resp.text}") from exc


def download_file(*, user_doc_id: str, file_name: str) -> Path:
    if not user_doc_id:
        raise ValueError(_bi("user_doc_id cannot be empty", "user_doc_id 不能为空"))

    url = f"{API_BASE}/v1/download"
    resp = requests.post(url, json={"user_doc_id": user_doc_id, "file_name": file_name}, timeout=60)
    if resp.status_code != 200:
        raise SpeedAIError(f"Download failed: HTTP {resp.status_code}: {resp.text}")

    out_path = Path(f"{file_name}.docx")
    out_path.write_bytes(resp.content)
    return out_path


def rewrite_text(*, apikey: str, text: str, lang: str, rewrite_type: str) -> str:
    payload = {"apikey": apikey, "info": text, "lang": lang, "type": rewrite_type}
    data = _post_json(f"{API_BASE}/v1/rewrite", payload)
    if data.get("code") != 200:
        raise SpeedAIError(f"Rewrite failed: {data}")
    return data["rewrite"]


# Backwards-compatible boolean flag helper for Python 3.8/3.9
def _add_bool_arg(parser: argparse.ArgumentParser, flag: str, *, default: bool, help: str) -> None:
    dest = flag.lstrip("-").replace("-", "_")
    if hasattr(argparse, "BooleanOptionalAction"):
        parser.add_argument(flag, action=argparse.BooleanOptionalAction, default=default, help=help)
    else:
        parser.add_argument(
            flag,
            dest=dest,
            action="store_const",
            const=True,
            default=default,
            help=f"Enable: {help}",
        )
        parser.add_argument(
            f"--no-{dest.replace('_', '-')}",
            dest=dest,
            action="store_const",
            const=False,
            help=f"Disable: {help}",
        )


def deai_text(*, apikey: str, text: str, lang: str, deai_type: str) -> str:
    payload = {"apikey": apikey, "info": text, "lang": lang, "type": deai_type}
    data = _post_json(f"{API_BASE}/v1/deai", payload)
    if data.get("code") != 200:
        raise SpeedAIError(f"DeAI failed: {data}")
    return data["rewrite"]


async def send_file(
    *,
    file_path: Path,
    apikey: str,
    mode: str,
    rewrite_type: str,
    changed_only: bool,
    skip_english: bool,
) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_details = {
        "FileName": file_path.name,
        "apikey": apikey,
        "mode": mode,                # [rewrite, deai]
        "type": rewrite_type,        # [zhiwang, weipu, gezida]
        "changed_only": changed_only,
        "skip_english": skip_english,
    }

    user_doc_id: Optional[str] = None
    ws_url = f"{WS_BASE}/v1/docx"
    async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as websocket:
        await websocket.send(json.dumps(file_details))
        with file_path.open("rb") as file:
            while True:
                chunk = file.read(1024 * 64)
                if not chunk:
                    break
                await websocket.send(chunk)

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data.get("status") == "error":
                raise SpeedAIError(f"WebSocket error: {data.get('error')}")
            if data.get("status") == "completed":
                user_doc_id = data.get("user_doc_id")
                break

            if "original" in data and "modified" in data:
                print(f"Original: {data['original']}")
                print(f"Modified: {data['modified']}")

    if not user_doc_id:
        raise SpeedAIError("No user_doc_id returned by server.")
    return user_doc_id


async def subscribe_docx_progress(*, token: str, doc_id: str, base_ws: str = AISURVEY_WS_BASE) -> None:
    token = (token or "").strip()
    doc_id = (doc_id or "").strip()
    if not token or not doc_id:
        raise ValueError(_bi("token and doc_id are required", "token 和 doc_id 必填"))

    query = urlencode({"token": token, "doc_id": doc_id, "snapshot_chunk_size": 50})
    ws_url = f"{base_ws.rstrip('/')}/v1/docx/progress?{query}"

    async with websockets.connect(ws_url) as websocket:
        while True:
            raw = await websocket.recv()
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            t = msg.get("type")
            if t in ("ping", "pong"):
                continue

            if t == "progress":
                print(f"[progress] doc_id={doc_id} {msg.get('progress')}% stage={msg.get('stage')}")
                continue

            if t == "paragraph":
                idx = msg.get("index")
                st = msg.get("status")
                if st == "processed":
                    print(f"[paragraph] #{idx} processed cost={msg.get('cost')}")
                elif st == "skipped":
                    print(f"[paragraph] #{idx} skipped reason={msg.get('skip_reason')}")
                else:
                    print(f"[paragraph] #{idx} status={st} detail={msg.get('detail') or msg.get('error')}")
                continue

            if t == "need_pay":
                print(f"[need_pay] {msg.get('message')} hint={msg.get('hint')}")
                break

            if t == "completed":
                print(_bi("[completed] Processing completed, use /v1/download to fetch", "[completed] 处理完成，可以调用 /v1/download 下载"))
                break

            if t == "error":
                print(f"[error] {msg.get('error')} detail={msg.get('detail')}")
                break

            print(f"[event] {msg}")


def parse_args() -> argparse.Namespace:
    default_text = (
        "有人说：“学生是一艘轮船，在知识的海洋中航行，能否顺利到达成功的彼岸，教师这个航标起到导航的关键作用。"
    )
    parser = argparse.ArgumentParser(description="SpeedAI API sample client")
    parser.add_argument("--file", default="文本.docx", help="Path to .docx file")
    parser.add_argument("--apikey", default=os.getenv("SPEEDAI_API_KEY", "test_api"))
    parser.add_argument("--mode", default="deai", choices=["rewrite", "deai"])
    parser.add_argument("--type", default="weipu", choices=["zhiwang", "weipu", "gezida"])
    parser.add_argument("--lang", default="Chinese", choices=["Chinese", "English"])
    parser.add_argument("--rewrite-text", default=default_text)
    parser.add_argument("--deai-text", default=default_text)
    parser.add_argument("--download-name", default="修改后论文")
    _add_bool_arg(parser, "--changed-only", default=True, help="Only return changed text")
    _add_bool_arg(parser, "--skip-english", default=False, help="Skip processing English text")
    parser.add_argument("--subscribe-token", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.apikey:
        raise SystemExit("Missing API key. Provide --apikey or set SPEEDAI_API_KEY.")

    file_path = Path(args.file)

    # 1) docx websocket processing → get user_doc_id
    user_doc_id = asyncio.run(
        send_file(
            file_path=file_path,
            apikey=args.apikey,
            mode=args.mode,
            rewrite_type=args.type,
            changed_only=args.changed_only,
            skip_english=args.skip_english,
        )
    )
    print(f"Download the modified document using id: {user_doc_id}")

    # 2) download the modified file
    downloaded = download_file(user_doc_id=user_doc_id, file_name=args.download_name)
    print(f"File downloaded successfully: {downloaded}")

    # 3) rewrite paragraph
    rewritten = rewrite_text(
        apikey=args.apikey, text=args.rewrite_text, lang=args.lang, rewrite_type=args.type
    )
    print(f"[rewrite]\n{rewritten}")

    # 4) deAI paragraph
    deai = deai_text(apikey=args.apikey, text=args.deai_text, lang=args.lang, deai_type=args.type)
    print(f"[deai]\n{deai}")

    # 5) optional progress subscription
    if args.subscribe_token:
        asyncio.run(subscribe_docx_progress(token=args.subscribe_token, doc_id=user_doc_id))


if __name__ == "__main__":
    try:
        main()
    except (SpeedAIError, FileNotFoundError) as exc:
        raise SystemExit(_bi(f"[SpeedAI] {exc}", "[SpeedAI] 发生错误，请检查输入或网络设置")) from exc
