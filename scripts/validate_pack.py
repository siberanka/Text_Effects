#!/usr/bin/env python3
"""Static validation for the multi-version Minecraft resource pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "assets/minecraft/shaders/include/_config.glsl"
ENTRY_RE = re.compile(
    r"^[ \t]*TEXT_EFFECT(?P<shadow>_WITH_SHADOW)?\s*\(\s*rgb\((?P<trigger>[^)]*)\)\s*\)\s*"
    r"\{(?P<body>.*?)\}",
    re.DOTALL | re.MULTILINE,
)
GRADIENT_RE = re.compile(
    r"apply_gradient\(\s*rgb\(([^)]*)\)\s*,\s*rgb\(([^)]*)\)\s*,\s*([0-9.]+)\s*\)"
)

RANK_GRADIENTS = {
    "F8F8DC": ((96, 96, 96), (255, 255, 255)),
    "F8F8E0": ((204, 156, 0), (255, 244, 128)),
    "F8F8E4": ((184, 72, 0), (255, 180, 92)),
    "F8F8E8": ((24, 96, 184), (64, 224, 255)),
    "F8F8EC": ((12, 32, 112), (64, 96, 192)),
    "F8F8F0": ((152, 24, 24), (255, 104, 104)),
    "F8F8F4": ((20, 112, 52), (96, 224, 132)),
    "F8F8F8": ((80, 28, 128), (176, 112, 232)),
    "F8F8FC": ((152, 48, 100), (255, 144, 196)),
    "F8FCDC": ((36, 36, 36), (128, 128, 128)),
    "F8FCE0": ((8, 8, 8), (72, 72, 72)),
    "F8FCE4": ((8, 64, 24), (52, 152, 76)),
    "F8FCE8": ((0, 88, 84), (72, 200, 192)),
    "F8FCEC": ((0, 112, 136), (112, 236, 248)),
    "F8FCF0": ((112, 24, 104), (232, 112, 220)),
    "F8FCF4": ((92, 52, 24), (188, 124, 76)),
}


class ValidationError(RuntimeError):
    pass


def rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().rstrip("uU")
    if value.lower().startswith("0x"):
        number = int(value, 16)
        return (number >> 16 & 0xFF, number >> 8 & 0xFF, number & 0xFF)
    parts = tuple(int(part.strip()) for part in value.split(","))
    if len(parts) != 3 or any(part < 0 or part > 255 for part in parts):
        raise ValidationError(f"Invalid RGB value: {value}")
    return parts


def hex_color(color: tuple[int, int, int]) -> str:
    return "".join(f"{part:02X}" for part in color)


def validate_metadata() -> None:
    metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
    pack = metadata["pack"]
    if pack.get("pack_format") != 16:
        raise ValidationError("pack.pack_format must remain 16 for the legacy fallback")
    expected_range = {"min_inclusive": 7, "max_inclusive": 100}
    if pack.get("supported_formats") != expected_range:
        raise ValidationError("supported_formats must cover resource formats 7 through 100")
    if (pack.get("min_format"), pack.get("max_format")) != (7, 100):
        raise ValidationError("modern min_format/max_format must remain 7/100")

    expected_overlays = [
        ("1_21_2", 36, 56),
        ("1_21_6", 57, 100),
        ("26_1", 76, 100),
        ("26_2", 85, 100),
    ]
    entries = metadata.get("overlays", {}).get("entries", [])
    actual = [
        (entry.get("directory"), entry.get("min_format"), entry.get("max_format"))
        for entry in entries
    ]
    if actual != expected_overlays:
        raise ValidationError(f"Unexpected overlay ranges: {actual!r}")
    for entry, (directory, minimum, maximum) in zip(entries, expected_overlays, strict=True):
        if entry.get("formats") != {"min_inclusive": minimum, "max_inclusive": maximum}:
            raise ValidationError(f"Legacy overlay range disagrees for {directory}")
        if not (ROOT / directory / "assets/minecraft/shaders").is_dir():
            raise ValidationError(f"Missing overlay shader tree: {directory}")


def validate_json_and_glsl() -> None:
    for path in ROOT.rglob("*.json"):
        if ".git" not in path.parts:
            json.loads(path.read_text(encoding="utf-8"))

    for extension in ("*.glsl", "*.vsh", "*.fsh"):
        for path in ROOT.rglob(extension):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            stripped = re.sub(r"//.*?$|/\*.*?\*/", "", text, flags=re.MULTILINE | re.DOTALL)
            if stripped.count("{") != stripped.count("}"):
                raise ValidationError(f"Unbalanced braces: {path.relative_to(ROOT)}")


def validate_color_registry() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    entries: dict[str, tuple[re.Match[str], tuple[int, int, int]]] = {}
    shadow_colors: dict[tuple[int, int, int], str] = {}

    for match in ENTRY_RE.finditer(config):
        trigger = rgb(match.group("trigger"))
        code = hex_color(trigger)
        if code in entries:
            raise ValidationError(f"Duplicate trigger color #{code}")
        entries[code] = (match, trigger)
        if match.group("shadow"):
            shadow = tuple(part // 4 for part in trigger)
            if shadow in shadow_colors:
                raise ValidationError(
                    f"Shadow collision: #{code} and #{shadow_colors[shadow]} -> #{hex_color(shadow)}"
                )
            shadow_colors[shadow] = code

    if len(entries) != 51:
        raise ValidationError(f"Expected 51 trigger colors, found {len(entries)}")

    main_colors = {value[1] for value in entries.values()}
    collisions = main_colors.intersection(shadow_colors)
    if collisions:
        raise ValidationError(f"Trigger/shadow color collision: {sorted(collisions)!r}")

    for code, expected in RANK_GRADIENTS.items():
        if code not in entries:
            raise ValidationError(f"Missing rank gradient trigger #{code}")
        match, trigger = entries[code]
        if not match.group("shadow"):
            raise ValidationError(f"Rank gradient #{code} must include its text shadow")
        if any(part % 4 for part in trigger):
            raise ValidationError(f"Rank gradient trigger #{code} is not divisible by four")
        gradient = GRADIENT_RE.search(match.group("body"))
        if not gradient:
            raise ValidationError(f"Rank gradient #{code} has no static gradient")
        actual = (rgb(gradient.group(1)), rgb(gradient.group(2)))
        if actual != expected or float(gradient.group(3)) != 4.0:
            raise ValidationError(f"Unexpected gradient definition for #{code}: {actual!r}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8").upper()
    missing = [f"#{code}" for code in entries if f"#{code}" not in readme]
    if missing:
        raise ValidationError(f"README is missing trigger codes: {', '.join(missing)}")


def validate_zip(path: Path) -> None:
    if not path.is_file():
        raise ValidationError(f"ZIP not found: {path}")
    allowed_roots = {
        "pack.mcmeta", "pack.png", "LICENSE", "assets", "1_21_2", "1_21_6", "26_1", "26_2"
    }
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            raise ValidationError("ZIP CRC validation failed")
        for name in names:
            pure = PurePosixPath(name)
            if name.startswith(("/", "\\")) or "\\" in name or ".." in pure.parts:
                raise ValidationError(f"Unsafe ZIP entry: {name}")
            if pure.parts and pure.parts[0] not in allowed_roots:
                raise ValidationError(f"Non-pack content in release ZIP: {name}")
        required = {"pack.mcmeta", "pack.png", "LICENSE"}
        if not required.issubset(names):
            raise ValidationError(f"ZIP root is missing: {sorted(required.difference(names))}")
        archived_meta = json.loads(archive.read("pack.mcmeta").decode("utf-8"))
        source_meta = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
        if archived_meta != source_meta:
            raise ValidationError("ZIP pack.mcmeta differs from the source tree")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, help="also validate a built release ZIP")
    args = parser.parse_args()
    validate_metadata()
    validate_json_and_glsl()
    validate_color_registry()
    if args.zip:
        validate_zip(args.zip.resolve())
    print("OK: metadata, overlays, JSON, GLSL structure, 51 colors, shadows, docs"
          + (", and release ZIP" if args.zip else ""))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
