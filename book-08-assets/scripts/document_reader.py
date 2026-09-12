"""Bounded local reader for synthetic PDF, DOCX and UTF-8 TXT files."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import zipfile


@dataclass(frozen=True)
class DocumentText:
    text: str
    file_sha256: str
    kind: str
    units: int
    warnings: tuple[str, ...] = ()


class DocumentReadError(ValueError):
    """A controlled input/format/limit error safe to map at a boundary."""


def _checked_file(path: str | Path, max_file_bytes: int) -> tuple[Path, bytes]:
    source = Path(path)
    if not source.is_file():
        raise DocumentReadError("file_not_found_or_not_regular")
    size = source.stat().st_size
    if size <= 0 or size > max_file_bytes:
        raise DocumentReadError("file_empty_or_too_large")
    data = source.read_bytes()
    if len(data) != size:
        raise DocumentReadError("file_changed_during_read")
    return source, data


def _finalize(text: str, data: bytes, kind: str, units: int, max_text_chars: int, warnings=()) -> DocumentText:
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines()).strip()
    if not normalized:
        raise DocumentReadError("no_extractable_text")
    if len(normalized) > max_text_chars:
        raise DocumentReadError("extracted_text_too_large")
    return DocumentText(normalized, hashlib.sha256(data).hexdigest(), kind, units, tuple(warnings))


def read_document(
    path: str | Path,
    *,
    max_file_bytes: int = 2_000_000,
    max_text_chars: int = 20_000,
    max_pdf_pages: int = 10,
    max_docx_entries: int = 200,
    max_docx_uncompressed: int = 10_000_000,
) -> DocumentText:
    source, data = _checked_file(path, max_file_bytes)
    suffix = source.suffix.casefold()

    if suffix == ".txt":
        try:
            text = data.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError as exc:
            raise DocumentReadError("txt_not_utf8") from exc
        return _finalize(text, data, "txt", 1, max_text_chars)

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("install pypdf to read PDF") from exc
        reader = PdfReader(source)
        if reader.is_encrypted:
            raise DocumentReadError("pdf_encrypted")
        if not 1 <= len(reader.pages) <= max_pdf_pages:
            raise DocumentReadError("pdf_page_limit")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return _finalize(text, data, "pdf", len(reader.pages), max_text_chars, ("text_layer_only_no_ocr",))

    if suffix == ".docx":
        try:
            from docx import Document
            from docx.table import Table
        except ImportError as exc:
            raise RuntimeError("install python-docx to read DOCX") from exc
        try:
            with zipfile.ZipFile(source) as archive:
                entries = archive.infolist()
                if len(entries) > max_docx_entries or sum(item.file_size for item in entries) > max_docx_uncompressed:
                    raise DocumentReadError("docx_expansion_limit")
        except zipfile.BadZipFile as exc:
            raise DocumentReadError("invalid_docx_package") from exc
        document = Document(source)
        blocks: list[str] = []
        for block in document.iter_inner_content():
            if isinstance(block, Table):
                blocks.extend(" | ".join(cell.text.strip() for cell in row.cells) for row in block.rows)
            else:
                blocks.append(block.text)
        return _finalize("\n".join(blocks), data, "docx", len(blocks), max_text_chars, ("images_and_complex_layout_not_ocr",))

    raise DocumentReadError("unsupported_file_type")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read one bounded local PDF, DOCX or UTF-8 TXT file")
    parser.add_argument("path")
    parser.add_argument("--preview-chars", type=int, default=160)
    args = parser.parse_args()
    if not 0 <= args.preview_chars <= 1_000:
        parser.error("--preview-chars must be between 0 and 1000")
    try:
        result = read_document(args.path)
    except (DocumentReadError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    payload = asdict(result)
    payload["text_chars"] = len(result.text)
    payload["preview"] = result.text[: args.preview_chars]
    del payload["text"]
    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
