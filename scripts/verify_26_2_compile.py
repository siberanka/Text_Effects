#!/usr/bin/env python3
"""Compile/link the supported Minecraft 26.2 and 26.3 text shader variants."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from shader_tools import (
    ResourceFormat, add_defines, client_resource_format, expand_includes,
    make_loader, overlay_roots, resolve_pack,
)


SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path("D:/ai/temp/text-effects-shader-compile")
BASE_VARIANTS = {
    "world": (),
    "world_grayscale": ("IS_GRAYSCALE",),
    "see_through": ("IS_SEE_THROUGH",),
    "see_through_grayscale": ("IS_SEE_THROUGH", "IS_GRAYSCALE"),
    "gui": ("IS_GUI",),
    "gui_grayscale": ("IS_GUI", "IS_GRAYSCALE"),
}
OIT_BASE = (
    "OIT", "OIT_COEFF_COUNT 8", "OIT_COEFF_ATTACHMENT_COUNT 2",
    "OIT_WAVELET_RANK 3",
)
OIT_VARIANTS = {
    "world_oit_accumulate": (*OIT_BASE, "OIT_ACCUMULATE"),
    "world_grayscale_oit_accumulate": (*OIT_BASE, "OIT_ACCUMULATE", "IS_GRAYSCALE"),
    "see_through_oit_accumulate": (*OIT_BASE, "OIT_ACCUMULATE", "IS_SEE_THROUGH"),
    "world_oit_depth_bounds": (*OIT_BASE, "OIT_DEPTH_BOUNDS", "OIT_ALPHA_ONLY"),
    "world_oit_transmittance": (*OIT_BASE, "OIT_TRANSMITTANCE", "OIT_ALPHA_ONLY"),
    "see_through_oit_transmittance": (
        *OIT_BASE, "OIT_TRANSMITTANCE", "OIT_ALPHA_ONLY", "IS_SEE_THROUGH",
    ),
}
MAX_ARCHIVE_ENTRIES = 10_000
MAX_ARCHIVE_ENTRY_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 256 * 1024 * 1024


def safe_extract(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise RuntimeError(f"ZIP has too many entries: {len(infos)}")
        total = 0
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            if name.startswith(("/", "\\")) or "\\" in name or ".." in pure.parts:
                raise RuntimeError(f"unsafe ZIP entry: {name}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise RuntimeError(f"ZIP symlink is not allowed: {name}")
            if info.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                raise RuntimeError(f"ZIP entry is too large: {name}")
            total += info.file_size
            if total > MAX_ARCHIVE_TOTAL_BYTES:
                raise RuntimeError("ZIP expanded size exceeds 256 MiB")
        archive.extractall(destination)


def safe_rmtree(path: Path) -> None:
    resolved = path.resolve()
    root = TEMP_ROOT.resolve()
    if root not in resolved.parents or resolved == root:
        raise RuntimeError(f"refusing to remove non-task temp path: {resolved}")
    shutil.rmtree(resolved)


def compile_root(args: argparse.Namespace, work: Path) -> Path:
    if args.pack_zip is None:
        return SOURCE_ROOT
    root = work / "pack"
    root.mkdir()
    safe_extract(args.pack_zip.resolve(), root)
    return root


def command_result(command: list[str], name: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{name} failed:\n{result.stdout}{result.stderr}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-jar", type=Path, required=True)
    parser.add_argument("--expected-client-sha1", required=True)
    parser.add_argument("--glslang", type=Path, required=True)
    parser.add_argument("--pack-zip", type=Path)
    args = parser.parse_args()
    client_jar = args.client_jar.resolve()
    glslang = args.glslang.resolve()
    if not client_jar.is_file():
        raise FileNotFoundError(client_jar)
    if not glslang.is_file():
        raise FileNotFoundError(glslang)
    actual_sha1 = hashlib.sha1(client_jar.read_bytes()).hexdigest()
    if actual_sha1.lower() != args.expected_client_sha1.lower():
        raise RuntimeError(f"Minecraft client SHA-1 mismatch: {actual_sha1}")

    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    work = TEMP_ROOT / uuid.uuid4().hex
    work.mkdir()
    try:
        root = compile_root(args, work)
        with zipfile.ZipFile(client_jar) as client:
            version = json.loads(client.read("version.json"))
            resource_format = client_resource_format(version)
            if resource_format not in (ResourceFormat(88), ResourceFormat(97, 1)):
                raise RuntimeError(
                    f"Expected Minecraft 26.2/26.3 resource format, got {resource_format}"
                )
            vertex_relative = "assets/minecraft/shaders/core/text.vsh"
            fragment_relative = "assets/minecraft/shaders/core/text.fsh"
            vertex_source = resolve_pack(root, vertex_relative, resource_format)
            fragment_source = resolve_pack(root, fragment_relative, resource_format)
            if vertex_source is None or fragment_source is None:
                raise RuntimeError("effective text shader entry points are missing")
            loader = make_loader(root, resource_format, client)
            vertex, _ = expand_includes(
                vertex_source.read_text(encoding="utf-8"), loader, deduplicate=True
            )
            fragment, _ = expand_includes(
                fragment_source.read_text(encoding="utf-8"), loader, deduplicate=True
            )
            variants = dict(BASE_VARIANTS)
            if resource_format >= ResourceFormat(97, 1):
                variants.update(OIT_VARIANTS)

            # 26.3's RenderPearl/Vulkan-flavoured source names the built-in
            # gl_VertexIndex. Desktop OpenGL glslang exposes the equivalent
            # base-inclusive value as gl_VertexID.
            backend_defines = (
                ("gl_VertexIndex gl_VertexID",)
                if resource_format >= ResourceFormat(97, 1)
                else ()
            )

            output = work / "expanded"
            output.mkdir()
            for name, defines in variants.items():
                vertex_path = output / f"{name}.vert"
                fragment_path = output / f"{name}.frag"
                vertex_text = add_defines(vertex, (*backend_defines, *defines))
                fragment_text = add_defines(fragment, (*backend_defines, *defines))
                vertex_path.write_text(vertex_text, encoding="utf-8")
                fragment_path.write_text(fragment_text, encoding="utf-8")
                pre_v = command_result([str(glslang), "-E", str(vertex_path)], f"{name} vertex preprocess")
                pre_f = command_result([str(glslang), "-E", str(fragment_path)], f"{name} fragment preprocess")
                if resource_format == ResourceFormat(88):
                    has_bias = bool(re.search(
                        r"gl_Position\s*\.\s*z\s*\+=\s*gl_Position\s*\.\s*w\s*\*\s*0\.001",
                        pre_v.stdout,
                    ))
                    if has_bias != name.startswith("world"):
                        raise RuntimeError(f"{name} has incorrect 26.2 depth-bias state")
                elif re.search(r"gl_Position\s*\.\s*z\s*[+-]=", pre_v.stdout):
                    raise RuntimeError(f"{name} copied a legacy depth bias into 26.3")
                command_result(
                    [str(glslang), "-l", str(vertex_path), str(fragment_path)],
                    f"{name} compile/link",
                )
                print(
                    f"OK {name:>34} | linked | preprocessed "
                    f"v={len(pre_v.stdout.encode('utf-8'))} f={len(pre_f.stdout.encode('utf-8'))} bytes"
                )
        print(
            f"OK: {len(variants)} Minecraft {version.get('id')} shader variants "
            f"against SHA-1 {actual_sha1}; overlays="
            + ",".join(path.name for path in overlay_roots(root, resource_format)[:-1])
        )
        return 0
    finally:
        safe_rmtree(work)


if __name__ == "__main__":
    raise SystemExit(main())
