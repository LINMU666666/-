"""
Robust requests crawler example with proxy controls.

Usage:
  python3 crawler_example.py https://example.com
  python3 crawler_example.py https://intranet --no-proxy
  python3 crawler_example.py https://corp --proxy http://proxy.host:8080 --verify-cert /path/to/cacert.pem
"""

from __future__ import annotations

import argparse
from typing import Dict, Optional, Tuple

import requests
from requests import Response
from requests.exceptions import ProxyError, RequestException, SSLError

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


class CrawlError(RuntimeError):
    """Raised when fetching a URL fails."""


def fetch_url(
    url: str,
    *,
    proxy: Optional[str] = None,
    disable_proxy: bool = False,
    verify_cert: Optional[str] = None,
    timeout: Tuple[float, float] = (5.0, 10.0),
) -> Response:
    """
    Fetch a URL with optional proxy overrides and certificate verification.

    Args:
        url: Target URL.
        proxy: Proxy URL (applied to both http/https). Example: http://proxy.host:8080
        disable_proxy: If True, ignore environment proxies.
        verify_cert: Path to CA bundle or PEM cert for TLS verification.
        timeout: (connect_timeout, read_timeout) seconds.
    """
    proxies = None
    if disable_proxy:
        proxies = {"http": None, "https": None}
    elif proxy:
        proxies = {"http": proxy, "https": proxy}

    try:
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            proxies=proxies,
            timeout=timeout,
            verify=verify_cert if verify_cert is not None else True,
        )
        resp.raise_for_status()
        return resp
    except ProxyError as exc:  # pragma: no cover - exercised via message path
        raise CrawlError(f"Proxy connection failed: {exc}") from exc
    except SSLError as exc:  # pragma: no cover - exercised via message path
        raise CrawlError(f"TLS/SSL failed: {exc}") from exc
    except RequestException as exc:
        raise CrawlError(f"Request failed: {exc}") from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal robust requests crawler demo.")
    parser.add_argument("url", help="Target URL to fetch")
    parser.add_argument("--proxy", help="Proxy URL, e.g. http://proxy.host:8080")
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        dest="no_proxy",
        help="Disable environment proxies (sets proxies={'http': None, 'https': None})",
    )
    parser.add_argument(
        "--verify-cert",
        metavar="PATH",
        help="Path to CA bundle or PEM file for TLS verification (recommended for corporate proxy)",
    )
    parser.add_argument(
        "--connect-timeout",
        type=float,
        default=5.0,
        help="Seconds for connection timeout (default: 5)",
    )
    parser.add_argument(
        "--read-timeout",
        type=float,
        default=10.0,
        help="Seconds for read timeout (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    timeout = (args.connect_timeout, args.read_timeout)
    resp = fetch_url(
        args.url,
        proxy=args.proxy,
        disable_proxy=args.no_proxy,
        verify_cert=args.verify_cert,
        timeout=timeout,
    )
    print(f"[ok] {args.url} status={resp.status_code} bytes={len(resp.content)}")


if __name__ == "__main__":
    main()
