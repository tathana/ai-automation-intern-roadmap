"""Small JSON HTTP client with explicit timeout and bounded transient retry."""
from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable

import httpx


class PermanentHTTPError(RuntimeError):
    pass


def request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    attempts: int = 3,
    timeout_seconds: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    if attempts < 1 or attempts > 5:
        raise ValueError("attempts_must_be_1_to_5")
    timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 3.0))
    last_error: Exception | None = None
    with httpx.Client(timeout=timeout, transport=transport) as client:
        for attempt in range(1, attempts + 1):
            try:
                response = client.request(method, url, json=payload, headers=headers)
                if response.status_code in {429, 502, 503, 504}:
                    raise httpx.HTTPStatusError("transient_status", request=response.request, response=response)
                if 400 <= response.status_code:
                    raise PermanentHTTPError(f"http_{response.status_code}")
                result = response.json()
                if not isinstance(result, dict):
                    raise PermanentHTTPError("response_not_json_object")
                return result
            except PermanentHTTPError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt == attempts:
                    break
                sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"transient_http_exhausted:{type(last_error).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description="GET a JSON object with bounded retry")
    parser.add_argument("url")
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()
    try:
        result = request_json("GET", args.url, attempts=args.attempts)
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "response": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
