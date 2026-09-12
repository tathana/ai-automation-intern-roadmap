"""Validated environment settings and privacy-aware structured logging."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
import os


@dataclass(frozen=True)
class Settings:
    database_path: str
    api_base_url: str
    http_timeout_seconds: float
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        timeout = float(os.environ.get("APP_HTTP_TIMEOUT_SECONDS", "5"))
        level = os.environ.get("APP_LOG_LEVEL", "INFO").upper()
        if not 0.1 <= timeout <= 60:
            raise ValueError("APP_HTTP_TIMEOUT_SECONDS must be 0.1..60")
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("APP_LOG_LEVEL is invalid")
        return cls(
            database_path=os.environ.get("APP_DATABASE_PATH", "data/app.sqlite3"),
            api_base_url=os.environ.get("APP_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            http_timeout_seconds=timeout,
            log_level=level,
        )


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        for field in ("event", "task_id", "correlation_id", "state", "attempt", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=getattr(logging, level), handlers=[handler], force=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect validated non-secret runtime settings")
    parser.add_argument("--show-config", action="store_true")
    args = parser.parse_args()
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    if args.show_config:
        print(json.dumps(asdict(settings), ensure_ascii=False, indent=2))
    logging.getLogger("runtime").info("runtime_ready", extra={"event": "startup", "state": "ready"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
