"""Persist optional deployment branding before Docker copies the project."""
import json
import os
from pathlib import Path
import re


def configure(root, environ):
    root = Path(root)
    path = root / "branding.json"
    brand = json.loads(path.read_text()) if path.exists() else {}
    for key in ("name", "tagline", "primary", "accent"):
        value = environ.get("BRAND_" + key.upper(), "").strip()
        if not value:
            continue
        if key in {"primary", "accent"} and not re.fullmatch(r"#[a-fA-F0-9]{6}", value):
            raise ValueError(f"BRAND_{key.upper()} must be a six-digit hex color")
        if len(value) > (80 if key == "name" else 200):
            raise ValueError(f"BRAND_{key.upper()} is too long")
        brand[key] = value
    logo = environ.get("BRAND_LOGO", "").strip()
    if logo:
        source = Path(logo)
        if source.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Logo must be at most 5 MiB")
        data = source.read_bytes()
        extension = "png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "jpg" if data.startswith(b"\xff\xd8\xff") else "webp" if data[:4] == b"RIFF" and data[8:12] == b"WEBP" else None
        if not extension:
            raise ValueError("Logo must be a PNG, JPEG or WebP image")
        brand["logo"] = f"core/brand/logo.{extension}"
        target = root / "core/static" / brand["logo"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    path.write_text(json.dumps(brand, indent=2) + "\n")


if __name__ == "__main__":
    configure(Path(__file__).resolve().parent.parent, os.environ)
