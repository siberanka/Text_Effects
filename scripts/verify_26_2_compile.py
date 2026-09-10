#!/usr/bin/env python3
"""Compile and link every Minecraft 26.2 text shader permutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORT_RE = re.compile(r"^[ \t]*#moj_import\s+<([^>]+)>[ \t]*$", re.MULTILINE)
VARIANTS = {
    "world": (),
    "world_grayscale": ("IS_GRAYSCALE",),
    "see_through": ("IS_SEE_THROUGH",),
    "see_through_grayscale": ("IS_SEE_THROUGH", "IS_GRAYSCALE"),
    "gui": ("IS_GUI",),
    "gui_grayscale": ("IS_GUI", "IS_GRAYSCALE"),
}


def overlay_roots() -> list[Path]:
    # These are the overlays active for resource format 88, in lookup order.
    return [ROOT / "26_2", ROOT / "1_21_6", ROOT]


def import_path(identifier: str) -> str:
    if ":" in identifier:
        namespace, relative = identifier.split(":", 1)
    else:
        namespace, relative = "minecraft", identifier
    return f"assets/{namespace}/shaders/include/{relative}"


def resolve_import(identifier: str, client: zipfile.ZipFile) -> tuple[str, str]:
    relative = import_path(identifier)
    for root in overlay_roots():
        candidate = root / relative
        if candidate.is_file():
            return relative, candidate.read_text(encoding="utf-8")
    try:
        return relative, client.read(relative).decode("utf-8")
    except KeyError as exc:
        raise RuntimeError(f"Unresolved shader import <{identifier}>") from exc


def expand_imports(
    text: str,
    client: zipfile.ZipFile,
    stack: tuple[str, ...] = (),
    imported_paths: set[str] | None = None,
) -> str:
    if imported_paths is None:
        imported_paths = set()

    def replace(match: re.Match[str]) -> str:
        relative, imported = resolve_import(match.group(1), client)
        if relative in stack:
            chain = " -> ".join((*stack, relative))
            raise RuntimeError(f"Recursive shader import: {chain}")
        if relative in imported_paths:
            return ""
        imported_paths.add(relative)
        # Mojang's 26.2 include files may carry their own #version directive;
        # the game's import processor removes it when composing a core shader.
        imported = re.sub(r"^#version[^\r\n]*(?:\r?\n)?", "", imported, count=1)
        return expand_imports(imported, client, (*stack, relative), imported_paths)

    return IMPORT_RE.sub(replace, text)


def add_defines(text: str, defines: tuple[str, ...]) -> str:
    # Apply GLSL's escaped-newline splicing before handing the expanded source
    # to glslang; Mojang's processor does the same for multiline macros.
    text = text.replace("\\\r\n", "").replace("\\\n", "")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("#version "):
        raise RuntimeError("Shader entry point has no #version directive")
    return "\n".join((lines[0], *(f"#define {name}" for name in defines), *lines[1:])) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-jar", type=Path, required=True)
    parser.add_argument("--expected-client-sha1", required=True)
    parser.add_argument("--glslang", type=Path, required=True)
    args = parser.parse_args()
    client_jar = args.client_jar.resolve()
    glslang = args.glslang.resolve()
    if not client_jar.is_file():
        raise FileNotFoundError(client_jar)
    if not glslang.is_file():
        raise FileNotFoundError(glslang)
    actual_sha1 = hashlib.sha1(client_jar.read_bytes()).hexdigest()
    if actual_sha1.lower() != args.expected_client_sha1.lower():
        raise RuntimeError(
            f"Minecraft 26.2 client SHA-1 mismatch: {actual_sha1}"
        )

    vertex_source = ROOT / "26_2/assets/minecraft/shaders/core/text.vsh"
    fragment_source = ROOT / "26_2/assets/minecraft/shaders/core/text.fsh"
    with zipfile.ZipFile(client_jar) as client, tempfile.TemporaryDirectory(
        prefix="text-effects-26.2-compile-"
    ) as directory:
        output = Path(directory)
        version = json.loads(client.read("version.json"))
        if version.get("id") != "26.2":
            raise RuntimeError(f"Expected Minecraft 26.2 client, got {version.get('id')!r}")
        resource_format = version["pack_version"].get("resource_major")
        if resource_format is None:
            resource = version["pack_version"]["resource"]
            resource_format = resource[0] if isinstance(resource, list) else resource
        if resource_format != 88:
            raise RuntimeError(f"Unexpected 26.2 resource format: {resource_format}")
        for source in (vertex_source, fragment_source):
            vanilla_path = f"assets/minecraft/shaders/core/{source.name}"
            vanilla_glsl = client.read(vanilla_path).decode("utf-8").splitlines()[0]
            pack_glsl = source.read_text(encoding="utf-8").splitlines()[0]
            if int(pack_glsl.split()[1]) < int(vanilla_glsl.split()[1]):
                raise RuntimeError(f"GLSL ABI is older than vanilla in {source.name}")
        vertex = expand_imports(vertex_source.read_text(encoding="utf-8"), client)
        fragment = expand_imports(fragment_source.read_text(encoding="utf-8"), client)
        for name, defines in VARIANTS.items():
            vertex_path = output / f"{name}.vert"
            fragment_path = output / f"{name}.frag"
            vertex_path.write_text(add_defines(vertex, defines), encoding="utf-8")
            fragment_path.write_text(add_defines(fragment, defines), encoding="utf-8")
            preprocessed = subprocess.run(
                [str(glslang), "-E", str(vertex_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if preprocessed.returncode:
                raise RuntimeError(
                    f"{name} failed to preprocess:\n"
                    f"{preprocessed.stdout}{preprocessed.stderr}"
                )
            has_reversed_depth_bias = bool(
                re.search(
                    r"gl_Position\s*\.\s*z\s*\+=\s*gl_Position\s*\.\s*w\s*\*\s*0\.001",
                    preprocessed.stdout,
                )
            )
            expects_reversed_depth_bias = name.startswith("world")
            if has_reversed_depth_bias != expects_reversed_depth_bias:
                raise RuntimeError(
                    f"{name} has incorrect 26.2 hologram depth-bias state"
                )
            result = subprocess.run(
                [str(glslang), "-l", str(vertex_path), str(fragment_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise RuntimeError(
                    f"{name} failed to compile/link:\n{result.stdout}{result.stderr}"
                )
            print(f"OK {name:>25} | compiled and linked")
    print(
        f"OK: {len(VARIANTS)} Minecraft 26.2 shader variants "
        f"against SHA-1 {actual_sha1}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
