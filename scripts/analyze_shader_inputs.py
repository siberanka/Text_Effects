#!/usr/bin/env python3
"""Measure fully expanded shader inputs and MemoryStack pressure."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path

from shader_tools import (
    ResourceFormat, add_defines, client_resource_format, expand_includes,
    make_loader, minify_glsl, overlay_roots, resolve_pack, shader_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path("D:/ai/temp/text-effects-shader-analysis")
ENTRIES = (
    "assets/minecraft/shaders/core/text.vsh",
    "assets/minecraft/shaders/core/text.fsh",
)


def parse_client(value: str) -> tuple[str, Path, str | None]:
    parts = value.split("=", 2)
    if len(parts) not in (2, 3):
        raise argparse.ArgumentTypeError("use VERSION=JAR_PATH[=EXPECTED_SHA1]")
    return parts[0], Path(parts[1]), parts[2] if len(parts) == 3 else None


def safe_rmtree(path: Path) -> None:
    resolved = path.resolve()
    root = TEMP_ROOT.resolve()
    if root not in resolved.parents or resolved == root:
        raise RuntimeError(f"refusing to remove non-task temp path: {resolved}")
    shutil.rmtree(resolved)


def preprocess(glslang: Path, source: str, suffix: str, work: Path) -> int:
    path = work / f"shader.{suffix}"
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [str(glslang), "-E", str(path)], check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise RuntimeError(f"preprocess failed for {suffix}:\n{result.stdout}{result.stderr}")
    return shader_bytes(result.stdout)


def analyze_mode(
    client: zipfile.ZipFile,
    resource_format: ResourceFormat,
    glslang: Path,
    work: Path,
    *,
    minified: bool,
) -> dict:
    base_loader = make_loader(ROOT, resource_format, client)

    def loader(identifier: str) -> str:
        text = base_loader(identifier)
        return minify_glsl(text) if minified else text

    measurements: dict[str, dict] = {}
    expanded_sources: dict[str, str] = {}
    for entry in ENTRIES:
        source_path = resolve_pack(ROOT, entry, resource_format)
        if source_path is None:
            raise RuntimeError(f"missing effective shader entry point: {entry}")
        source = source_path.read_text(encoding="utf-8")
        if minified:
            source = minify_glsl(source)
        expanded, stats = expand_includes(source, loader)
        expanded_sources[entry] = expanded
        stage = "vert" if entry.endswith(".vsh") else "frag"
        defines: tuple[str, ...] = ()
        if resource_format >= ResourceFormat(97, 1) and stage == "frag":
            defines = (
                "OIT", "OIT_COEFF_COUNT 8", "OIT_COEFF_ATTACHMENT_COUNT 2",
                "OIT_WAVELET_RANK 3", "OIT_ACCUMULATE",
            )
        prepared = add_defines(expanded, defines)
        measurements[stage] = {
            "entry_utf8_bytes": shader_bytes(source),
            "expanded_utf8_bytes": shader_bytes(expanded),
            "preprocessed_utf8_bytes": preprocess(glslang, prepared, stage, work),
            "include_occurrences": sum(stats.occurrences.values()),
            "unique_includes": len(stats.occurrences),
            "duplicate_includes": stats.duplicates,
            "max_include_depth": max((len(chain) for chain in stats.chains), default=0),
        }

    vertex = measurements["vert"]["expanded_utf8_bytes"]
    fragment = measurements["frag"]["expanded_utf8_bytes"]
    return {
        "stages": measurements,
        # MemoryStack.UTF8 stores a NUL-terminated UTF-8 buffer. This is the
        # two-source lower bound when both allocations share one stack frame;
        # native compiler options/pointers may add further allocations.
        "simultaneous_utf8_nul_bytes_lower_bound": vertex + 1 + fragment + 1,
        "lwjgl_default_stack_bytes": 64 * 1024,
        "fits_default_stack_lower_bound": vertex + fragment + 2 <= 64 * 1024,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", action="append", type=parse_client, required=True)
    parser.add_argument("--glslang", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    glslang = args.glslang.resolve()
    if not glslang.is_file():
        raise FileNotFoundError(glslang)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    work = TEMP_ROOT / uuid.uuid4().hex
    work.mkdir()
    report: dict[str, dict] = {}
    try:
        for version, jar_path, expected_sha1 in args.client:
            jar_path = jar_path.resolve()
            digest = hashlib.sha1(jar_path.read_bytes()).hexdigest()
            if expected_sha1 and digest.lower() != expected_sha1.lower():
                raise RuntimeError(f"{version}: client SHA-1 mismatch: {digest}")
            with zipfile.ZipFile(jar_path) as client:
                version_json = json.loads(client.read("version.json"))
                if version_json.get("id") != version:
                    raise RuntimeError(
                        f"client label {version!r} differs from JAR {version_json.get('id')!r}"
                    )
                resource_format = client_resource_format(version_json)
                version_work = work / version.replace(".", "_")
                version_work.mkdir()
                report[version] = {
                    "client_sha1": digest,
                    "resource_format": str(resource_format),
                    "overlay_lookup": [
                        str(path.relative_to(ROOT)) if path != ROOT else "."
                        for path in overlay_roots(ROOT, resource_format)
                    ],
                    "source": analyze_mode(
                        client, resource_format, glslang, version_work, minified=False
                    ),
                    "release_minified": analyze_mode(
                        client, resource_format, glslang, version_work, minified=True
                    ),
                }
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
            args.output.resolve().write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0
    finally:
        safe_rmtree(work)


if __name__ == "__main__":
    raise SystemExit(main())
