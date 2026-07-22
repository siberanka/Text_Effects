#!/usr/bin/env python3
"""Build a deterministic, Minecraft-ready resource-pack ZIP."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOTS = (
    "pack.mcmeta", "pack.png", "LICENSE", "assets", "1_21_2", "1_21_6", "26_1", "26_2"
)
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def source_files() -> list[Path]:
    files: list[Path] = []
    for name in PACK_ROOTS:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
        else:
            raise FileNotFoundError(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in source_files():
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
