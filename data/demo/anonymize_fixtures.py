from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {
    "name",
    "supplier",
    "supplier_name",
    "owner",
    "phone",
    "mobile",
    "email",
    "address",
    "title",
}

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"\d{7,}")


def alias(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest.upper()}"


def sanitize_value(key: str, value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return value

    lowered = key.lower()
    if lowered in {"email"} or EMAIL_RE.match(text):
        return f"{alias('email', text).lower()}@example.com"
    if lowered in {"phone", "mobile"} or PHONE_RE.search(text):
        return "+91-XXXX-XXXX"
    if lowered in {"address"}:
        return alias("address", text)
    if lowered in {"name", "supplier", "supplier_name", "owner", "title"}:
        return alias(lowered, text)
    return value


def sanitize_json(value: Any, parent_key: str = "") -> Any:
    if isinstance(value, dict):
        return {
            key: sanitize_json(child, key)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [sanitize_json(item, parent_key) for item in value]
    return sanitize_value(parent_key, value)


def sanitize_csv(path: Path, in_place: bool) -> Path:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    sanitized_rows: list[dict[str, Any]] = []
    for row in rows:
        sanitized_rows.append(
            {
                key: sanitize_value(key, value)
                for key, value in row.items()
            }
        )

    output = path if in_place else path.with_stem(f"{path.stem}-sanitized")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sanitized_rows)
    return output


def sanitize_json_file(path: Path, in_place: bool) -> Path:
    value = json.loads(path.read_text(encoding="utf-8"))
    sanitized = sanitize_json(value)
    output = path if in_place else path.with_stem(f"{path.stem}-sanitized")
    output.write_text(json.dumps(sanitized, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanitize demo fixture files before committing them."
    )
    parser.add_argument("path", type=Path, help="Path to CSV or JSON fixture")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the source file instead of writing a -sanitized copy",
    )
    args = parser.parse_args()

    target = args.path
    if not target.exists():
        raise SystemExit(f"File not found: {target}")

    suffix = target.suffix.lower()
    if suffix == ".csv":
        output = sanitize_csv(target, args.in_place)
    elif suffix == ".json":
        output = sanitize_json_file(target, args.in_place)
    else:
        raise SystemExit("Only CSV and JSON fixtures are supported.")

    print(f"Sanitized fixture written to: {output}")


if __name__ == "__main__":
    main()
