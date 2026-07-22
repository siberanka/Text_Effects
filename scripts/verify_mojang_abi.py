#!/usr/bin/env python3
"""Verify pack shader entry points against SHA-1-checked official client JARs.

This is intentionally not part of regular CI because it downloads multiple
Minecraft clients. It checks the release-family boundaries where text shaders
or pack metadata changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import ssl
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEFAULT_VERSIONS = (
    "1.17.1",
    "1.21.1",
    "1.21.2",
    "1.21.5",
    "1.21.6",
    "1.21.8",
    "1.21.9",
    "1.21.11",
    "26.1.1",
    "26.2",
)
LEGACY_TEXT_SHADERS = tuple(
    f"assets/minecraft/shaders/core/{name}.{extension}"
    for name in (
        "rendertype_text",
        "rendertype_text_see_through",
        "rendertype_text_intensity",
        "rendertype_text_intensity_see_through",
    )
    for extension in ("vsh", "fsh")
)
COMBINED_TEXT_SHADERS = (
    "assets/minecraft/shaders/core/text.vsh",
    "assets/minecraft/shaders/core/text.fsh",
)
IMPORT_RE = re.compile(r"#moj_import\s+<([^>]+)>")
INPUT_RE = re.compile(r"^\s*in\s+\w+\s+(\w+)\s*;", re.MULTILINE)
SSL_CONTEXT = ssl.create_default_context()
# Python 3.13+ enables OpenSSL strict verification on some platforms. The
# Windows trust store can contain otherwise valid CAs whose Basic Constraints
# extension is not marked critical. Keep chain and hostname verification, but
# disable only that extra strictness for Mojang's HTTPS endpoints.
if hasattr(ssl, "VERIFY_X509_STRICT"):
    SSL_CONTEXT.verify_flags &= ~ssl.VERIFY_X509_STRICT


def load_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60, context=SSL_CONTEXT) as response:
        return json.load(response)


def download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=120, context=SSL_CONTEXT) as response:
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def major_pack_format(value: object) -> int:
    if isinstance(value, list):
        return int(value[0])
    return int(value)


def overlay_roots(pack_format: int) -> list[Path]:
    metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
    active: list[Path] = []
    for entry in metadata["overlays"]["entries"]:
        if entry["min_format"] <= pack_format <= entry["max_format"]:
            active.append(ROOT / entry["directory"])
    return list(reversed(active)) + [ROOT]


def resolve_pack(path: str, pack_format: int) -> Path | None:
    for root in overlay_roots(pack_format):
        candidate = root / path
        if candidate.is_file():
            return candidate
    return None


def import_path(identifier: str) -> str:
    if ":" in identifier:
        namespace, relative = identifier.split(":", 1)
    else:
        namespace, relative = "minecraft", identifier
    return f"assets/{namespace}/shaders/include/{relative}"


def verify_imports(
    text: str,
    pack_format: int,
    vanilla: zipfile.ZipFile,
    visited: set[str],
) -> None:
    vanilla_names = set(vanilla.namelist())
    for identifier in IMPORT_RE.findall(text):
        path = import_path(identifier)
        if path in visited:
            continue
        visited.add(path)
        source = resolve_pack(path, pack_format)
        if source:
            imported = source.read_text(encoding="utf-8")
        elif path in vanilla_names:
            imported = vanilla.read(path).decode("utf-8")
        else:
            raise RuntimeError(f"unresolved import <{identifier}> ({path})")
        verify_imports(imported, pack_format, vanilla, visited)


def verify_version(version: str, metadata_url: str, work: Path) -> tuple[int, str]:
    metadata = load_json(metadata_url)
    client = metadata["downloads"]["client"]
    jar_path = work / f"{version}.jar"
    download(client["url"], jar_path)
    digest = hashlib.sha1(jar_path.read_bytes()).hexdigest()
    if digest != client["sha1"]:
        raise RuntimeError(f"{version}: client JAR SHA-1 mismatch")

    with zipfile.ZipFile(jar_path) as vanilla:
        version_json = json.loads(vanilla.read("version.json"))
        pack_versions = version_json["pack_version"]
        if "resource" in pack_versions:
            pack_format = major_pack_format(pack_versions["resource"])
        elif "resource_major" in pack_versions:
            pack_format = int(pack_versions["resource_major"])
        else:
            raise RuntimeError(f"{version}: unknown pack_version schema: {pack_versions!r}")
        checked = 0
        shader_paths = COMBINED_TEXT_SHADERS if pack_format >= 85 else LEGACY_TEXT_SHADERS
        for path in shader_paths:
            source = resolve_pack(path, pack_format)
            if source is None:
                raise RuntimeError(f"{version}: pack has no effective {path}")
            if path not in vanilla.namelist():
                raise RuntimeError(f"{version}: vanilla client has no {path}")
            pack_text = source.read_text(encoding="utf-8")
            vanilla_text = vanilla.read(path).decode("utf-8")
            pack_version = pack_text.splitlines()[0].strip()
            vanilla_version = vanilla_text.splitlines()[0].strip()
            pack_glsl = int(pack_version.removeprefix("#version ").split()[0])
            vanilla_glsl = int(vanilla_version.removeprefix("#version ").split()[0])
            if pack_glsl < vanilla_glsl:
                raise RuntimeError(
                    f"{version}: GLSL version mismatch in {Path(path).name}: "
                    f"{pack_version!r} != {vanilla_version!r}"
                )
            if path.endswith(".vsh"):
                pack_inputs = set(INPUT_RE.findall(pack_text))
                # Until resource format 56, core-program JSON explicitly
                # declares attribute bindings, so validate their consistency.
                # Newer fixed pipelines may expose attributes that the stock
                # vanilla shader simply does not consume; source comparison
                # cannot prove those attributes absent from the vertex format.
                if pack_format <= 56:
                    config_path = path.removesuffix(".vsh") + ".json"
                    config_source = resolve_pack(config_path, pack_format)
                    if config_source is None:
                        raise RuntimeError(f"{version}: missing program config {config_path}")
                    attributes = set(json.loads(config_source.read_text(encoding="utf-8"))["attributes"])
                    extra_inputs = pack_inputs - attributes
                else:
                    extra_inputs = set()
                if extra_inputs:
                    raise RuntimeError(
                        f"{version}: unsupported vertex inputs in {Path(path).name}: {sorted(extra_inputs)}"
                    )
            verify_imports(pack_text, pack_format, vanilla, set())
            checked += 1
    return pack_format, f"{checked} shader entry points"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-snapshot", action="store_true")
    parser.add_argument("versions", nargs="*")
    args = parser.parse_args()
    manifest = load_json(MANIFEST_URL)
    versions = list(args.versions or DEFAULT_VERSIONS)
    if args.include_snapshot:
        versions.append(manifest["latest"]["snapshot"])
    urls = {entry["id"]: entry["url"] for entry in manifest["versions"]}

    with tempfile.TemporaryDirectory(prefix="text-effects-mojang-") as directory:
        for version in versions:
            if version not in urls:
                raise RuntimeError(f"Version not found in Mojang manifest: {version}")
            pack_format, detail = verify_version(version, urls[version], Path(directory))
            print(f"OK {version:>18} | resource format {pack_format:>3} | {detail}")
    print(f"OK: {len(versions)} SHA-1-verified official clients")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
