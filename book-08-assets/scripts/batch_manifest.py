"""Create a bounded, relative-path manifest without following symlinks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path, chunk_bytes: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: str | Path, extensions: set[str], *, max_files: int = 1_000, max_each_bytes: int = 5_000_000) -> list[dict]:
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("root_not_directory")
    allowed = {value.casefold() if value.startswith(".") else "." + value.casefold() for value in extensions}
    rows: list[dict] = []
    for path in sorted(base.rglob("*")):
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in allowed:
            continue
        size = path.stat().st_size
        if size > max_each_bytes:
            rows.append({"path": path.relative_to(base).as_posix(), "size": size, "state": "too_large", "sha256": None})
        else:
            rows.append({"path": path.relative_to(base).as_posix(), "size": size, "state": "ready", "sha256": sha256_file(path)})
        if len(rows) > max_files:
            raise ValueError("file_limit_exceeded")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory files before batch processing")
    parser.add_argument("root")
    parser.add_argument("--extension", nargs="+", default=[".pdf", ".docx", ".txt", ".csv", ".json", ".xlsx"])
    parser.add_argument("--max-files", type=int, default=1_000)
    args = parser.parse_args()
    try:
        manifest = build_manifest(args.root, set(args.extension), max_files=args.max_files)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "files": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
