#!/usr/bin/env python3
"""Build a deterministic, Minecraft-ready resource-pack ZIP."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from shader_tools import minify_glsl


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOTS = (
    "pack.mcmeta", "pack.png", "LICENSE", "assets", "1_21_2", "1_21_6", "26_1", "26_2",
    "26_3",
)
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def source_files() -> list[Path]:
    files: list[Path] = []
    resolved_root = ROOT.resolve()
    for name in PACK_ROOTS:
        path = ROOT / name
        if path.is_file():
            if path.is_symlink():
                raise RuntimeError(f"release input must not be a symlink: {path}")
            files.append(path)
        elif path.is_dir():
            for item in path.rglob("*"):
                if item.is_symlink():
                    raise RuntimeError(f"release input must not be a symlink: {item}")
                if item.is_file():
                    try:
                        item.resolve(strict=True).relative_to(resolved_root)
                    except ValueError as exc:
                        raise RuntimeError(f"release input escapes repository: {item}") from exc
                    files.append(item)
        else:
            raise FileNotFoundError(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--no-minify-shaders",
        action="store_true",
        help="preserve shader comments and blank lines in the archive",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    files = source_files()
    for name in PACK_ROOTS:
        pack_root = (ROOT / name).resolve()
        if (ROOT / name).is_dir() and (output == pack_root or pack_root in output.parents):
            raise RuntimeError(f"release output must be outside packaged roots: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            data = path.read_bytes()
            if not args.no_minify_shaders and path.suffix in {".glsl", ".vsh", ".fsh"}:
                data = minify_glsl(data.decode("utf-8")).encode("utf-8")
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
