#!/usr/bin/env python3
"""Verify pack shader entry points against SHA-1-checked official clients."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import ssl
import urllib.request
import zipfile
from pathlib import Path

from shader_tools import (
    INCLUDE_RE, ResourceFormat, client_resource_format, include_path,
    layout_interface, overlay_roots, resolve_pack,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEFAULT_CACHE = Path("D:/ai/cache/text-effects-mojang")
DEFAULT_VERSIONS = (
    "1.17.1", "1.21.1", "1.21.2", "1.21.5", "1.21.6", "1.21.8",
    "1.21.9", "1.21.11", "26.1.1", "26.2", "26.3",
)
LEGACY_TEXT_SHADERS = tuple(
    f"assets/minecraft/shaders/core/{name}.{extension}"
    for name in (
        "rendertype_text", "rendertype_text_see_through",
        "rendertype_text_intensity", "rendertype_text_intensity_see_through",
    )
    for extension in ("vsh", "fsh")
)
COMBINED_TEXT_SHADERS = (
    "assets/minecraft/shaders/core/text.vsh",
    "assets/minecraft/shaders/core/text.fsh",
)
PLAIN_INPUT_RE = re.compile(r"^\s*in\s+\w+\s+(\w+)\s*;", re.MULTILINE)
SSL_CONTEXT = ssl.create_default_context()
if hasattr(ssl, "VERIFY_X509_STRICT"):
    SSL_CONTEXT.verify_flags &= ~ssl.VERIFY_X509_STRICT


def load_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60, context=SSL_CONTEXT) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    with urllib.request.urlopen(url, timeout=120, context=SSL_CONTEXT) as response:
        with partial.open("wb") as output:
            shutil.copyfileobj(response, output)
    partial.replace(destination)


def verify_includes(
    text: str,
    resource_format: ResourceFormat,
    vanilla: zipfile.ZipFile,
    stack: tuple[str, ...] = (),
    visited: set[str] | None = None,
) -> None:
    if visited is None:
        visited = set()
    vanilla_names = set(vanilla.namelist())
    for identifier in INCLUDE_RE.findall(text):
        relative = include_path(identifier)
        if relative in stack:
            raise RuntimeError(f"recursive include: {' -> '.join((*stack, relative))}")
        if relative in visited:
            continue
        visited.add(relative)
        source = resolve_pack(ROOT, relative, resource_format)
        if source is not None:
            imported = source.read_text(encoding="utf-8")
        elif relative in vanilla_names:
            imported = vanilla.read(relative).decode("utf-8")
        else:
            raise RuntimeError(f"unresolved include <{identifier}> ({relative})")
        verify_includes(imported, resource_format, vanilla, (*stack, relative), visited)


def verify_explicit_26_3_abi(pack_vertex: str, pack_fragment: str, vanilla_vertex: str) -> None:
    pack_inputs = layout_interface(pack_vertex, "in")
    vanilla_inputs = layout_interface(vanilla_vertex, "in")
    if not pack_inputs or not vanilla_inputs:
        raise RuntimeError("26.3 explicit vertex layouts were not detected")
    for location, (data_type, name) in pack_inputs.items():
        official = vanilla_inputs.get(location)
        if official is None or official[0] != data_type:
            raise RuntimeError(
                f"26.3 vertex input location {location} ({data_type} {name}) "
                f"does not match vanilla {official!r}"
            )

    vertex_outputs = layout_interface(pack_vertex, "out")
    fragment_inputs = layout_interface(pack_fragment, "in")
    if set(vertex_outputs) != set(fragment_inputs):
        raise RuntimeError(
            "26.3 vertex/fragment locations differ: "
            f"vsh-only={sorted(set(vertex_outputs) - set(fragment_inputs))}, "
            f"fsh-only={sorted(set(fragment_inputs) - set(vertex_outputs))}"
        )
    for location, (data_type, _) in vertex_outputs.items():
        if fragment_inputs[location][0] != data_type:
            raise RuntimeError(f"26.3 interface type mismatch at location {location}")


def cached_client(version: str, metadata: dict, cache: Path) -> Path:
    client = metadata["downloads"]["client"]
    jar_path = cache / version / "client.jar"
    if not jar_path.is_file() or hashlib.sha1(jar_path.read_bytes()).hexdigest() != client["sha1"]:
        download(client["url"], jar_path)
    digest = hashlib.sha1(jar_path.read_bytes()).hexdigest()
    if digest != client["sha1"]:
        raise RuntimeError(f"{version}: client JAR SHA-1 mismatch")
    return jar_path


def verify_version(version: str, metadata_url: str, cache: Path) -> tuple[ResourceFormat, str]:
    metadata = load_json(metadata_url)
    jar_path = cached_client(version, metadata, cache)
    with zipfile.ZipFile(jar_path) as vanilla:
        version_json = json.loads(vanilla.read("version.json"))
        resource_format = client_resource_format(version_json)
        shader_paths = COMBINED_TEXT_SHADERS if resource_format.major >= 88 else LEGACY_TEXT_SHADERS
        pack_sources: dict[str, str] = {}
        vanilla_sources: dict[str, str] = {}
        for path in shader_paths:
            source = resolve_pack(ROOT, path, resource_format)
            if source is None:
                raise RuntimeError(f"{version}: pack has no effective {path}")
            if path not in vanilla.namelist():
                raise RuntimeError(f"{version}: vanilla client has no {path}")
            pack_text = source.read_text(encoding="utf-8")
            vanilla_text = vanilla.read(path).decode("utf-8")
            pack_sources[path] = pack_text
            vanilla_sources[path] = vanilla_text
            pack_glsl = int(pack_text.splitlines()[0].removeprefix("#version ").split()[0])
            vanilla_glsl = int(vanilla_text.splitlines()[0].removeprefix("#version ").split()[0])
            if pack_glsl < vanilla_glsl:
                raise RuntimeError(f"{version}: GLSL version is older than vanilla in {Path(path).name}")
            if path.endswith(".vsh") and resource_format.major <= 56:
                config_path = path.removesuffix(".vsh") + ".json"
                config_source = resolve_pack(ROOT, config_path, resource_format)
                if config_source is None:
                    raise RuntimeError(f"{version}: missing program config {config_path}")
                attributes = set(json.loads(config_source.read_text(encoding="utf-8"))["attributes"])
                extra = set(PLAIN_INPUT_RE.findall(pack_text)) - attributes
                if extra:
                    raise RuntimeError(
                        f"{version}: unsupported vertex inputs in {Path(path).name}: {sorted(extra)}"
                    )
            verify_includes(pack_text, resource_format, vanilla)

        if resource_format >= ResourceFormat(97, 1):
            verify_explicit_26_3_abi(
                pack_sources[COMBINED_TEXT_SHADERS[0]],
                pack_sources[COMBINED_TEXT_SHADERS[1]],
                vanilla_sources[COMBINED_TEXT_SHADERS[0]],
            )
        roots = ",".join(path.name for path in overlay_roots(ROOT, resource_format)[:-1])
        return resource_format, f"{len(shader_paths)} entry points; overlays={roots}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-snapshot", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("versions", nargs="*")
    args = parser.parse_args()
    manifest = load_json(MANIFEST_URL)
    versions = list(args.versions or DEFAULT_VERSIONS)
    if args.include_snapshot:
        versions.append(manifest["latest"]["snapshot"])
    urls = {entry["id"]: entry["url"] for entry in manifest["versions"]}
    for version in versions:
        if version not in urls:
            raise RuntimeError(f"version not found in Mojang manifest: {version}")
        resource_format, detail = verify_version(version, urls[version], args.cache_dir.resolve())
        print(f"OK {version:>18} | resource format {str(resource_format):>6} | {detail}")
    print(f"OK: {len(versions)} SHA-1-verified official clients")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
