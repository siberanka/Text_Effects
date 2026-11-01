#!/usr/bin/env python3
"""Shared resource-format and shader preprocessing helpers."""

from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Callable


INCLUDE_RE = re.compile(
    r"^[ \t]*#(?:moj_import|include)[ \t]+<([^>]+)>[ \t]*$", re.MULTILINE
)
LAYOUT_IO_RE = re.compile(
    r"^[ \t]*(?:layout[ \t]*\([ \t]*location[ \t]*=[ \t]*(\d+)[ \t]*\)[ \t]*)?"
    r"(in|out)[ \t]+([A-Za-z_]\w*)[ \t]+([A-Za-z_]\w*)[ \t]*;",
    re.MULTILINE,
)
TOKEN_RE = re.compile(
    r"(?:0[xX][0-9A-Fa-f]+[uU]?|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fFuU]?)"
    r"|(?:[A-Za-z_]\w*)"
    r"|(?:<<=|>>=|\+\+|--|==|!=|<=|>=|&&|\|\||\^\^|\+=|-=|\*=|/=|%=|"
    r"&=|\^=|\|=|<<|>>)"
    r"|(?:[{}()\[\];,.])"
    r"|(?:[=+\-*/<>!?:&|%^~])"
    r"|(?:\S)"
)
WORD_RE = re.compile(r"^(?:[A-Za-z_]\w*|(?:0[xX][0-9A-Fa-f]+[uU]?|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fFuU]?))$")
OPERATOR_RE = re.compile(r"^[=+\-*/<>!?:&|%^~]+$")


@dataclass(frozen=True, order=True)
class ResourceFormat:
    major: int
    minor: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}" if self.minor else str(self.major)


def parse_format(value: object, *, upper_bound: bool = False) -> ResourceFormat:
    if isinstance(value, list):
        if len(value) != 2:
            raise ValueError(f"invalid major/minor resource format: {value!r}")
        return ResourceFormat(int(value[0]), int(value[1]))
    return ResourceFormat(int(value), 2_147_483_647 if upper_bound else 0)


def client_resource_format(version_json: dict) -> ResourceFormat:
    versions = version_json["pack_version"]
    if "resource_major" in versions:
        return ResourceFormat(
            int(versions["resource_major"]), int(versions.get("resource_minor", 0))
        )
    resource = versions["resource"]
    return parse_format(resource)


def overlay_roots(root: Path, resource_format: ResourceFormat) -> list[Path]:
    metadata = json.loads((root / "pack.mcmeta").read_text(encoding="utf-8"))
    active: list[Path] = []
    for entry in metadata.get("overlays", {}).get("entries", []):
        minimum = parse_format(entry["min_format"])
        maximum = parse_format(entry["max_format"], upper_bound=True)
        if minimum <= resource_format <= maximum:
            active.append(root / entry["directory"])
    return list(reversed(active)) + [root]


def resolve_pack(root: Path, relative: str, resource_format: ResourceFormat) -> Path | None:
    for candidate_root in overlay_roots(root, resource_format):
        candidate = candidate_root / relative
        if candidate.is_file():
            return candidate
    return None


def include_path(identifier: str) -> str:
    if ":" in identifier:
        namespace, relative = identifier.split(":", 1)
    else:
        namespace, relative = "minecraft", identifier
    if not re.fullmatch(r"[a-z0-9_.-]+", namespace):
        raise RuntimeError(f"invalid shader include namespace: {namespace!r}")
    if "\\" in relative:
        raise RuntimeError(f"invalid shader include path: {relative!r}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise RuntimeError(f"invalid shader include path: {relative!r}")
    return f"assets/{namespace}/shaders/include/{relative}"


@dataclass
class ExpansionStats:
    occurrences: Counter[str] = field(default_factory=Counter)
    chains: list[tuple[str, ...]] = field(default_factory=list)

    @property
    def duplicates(self) -> dict[str, int]:
        return {name: count for name, count in self.occurrences.items() if count > 1}


Loader = Callable[[str], str]


def make_loader(
    root: Path, resource_format: ResourceFormat, client: zipfile.ZipFile
) -> Loader:
    vanilla_names = set(client.namelist())

    def load(identifier: str) -> str:
        relative = include_path(identifier)
        source = resolve_pack(root, relative, resource_format)
        if source is not None:
            return source.read_text(encoding="utf-8")
        if relative in vanilla_names:
            return client.read(relative).decode("utf-8")
        raise RuntimeError(f"unresolved shader include <{identifier}> ({relative})")

    return load


def expand_includes(
    text: str,
    loader: Loader,
    *,
    stack: tuple[str, ...] = (),
    stats: ExpansionStats | None = None,
    deduplicate: bool = False,
    imported_paths: set[str] | None = None,
) -> tuple[str, ExpansionStats]:
    if stats is None:
        stats = ExpansionStats()
    if imported_paths is None:
        imported_paths = set()

    def replace(match: re.Match[str]) -> str:
        identifier = match.group(1)
        relative = include_path(identifier)
        if relative in stack:
            chain = " -> ".join((*stack, relative))
            raise RuntimeError(f"recursive shader include: {chain}")
        stats.occurrences[relative] += 1
        stats.chains.append((*stack, relative))
        if deduplicate and relative in imported_paths:
            return ""
        imported_paths.add(relative)
        imported = loader(identifier)
        imported = re.sub(r"^#version[^\r\n]*(?:\r?\n)?", "", imported, count=1)
        expanded, _ = expand_includes(
            imported,
            loader,
            stack=(*stack, relative),
            stats=stats,
            deduplicate=deduplicate,
            imported_paths=imported_paths,
        )
        return expanded

    return INCLUDE_RE.sub(replace, text), stats


def add_defines(text: str, defines: tuple[str, ...]) -> str:
    # GLSL line splicing happens before directive parsing.
    text = text.replace("\\\r\n", "").replace("\\\n", "")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("#version "):
        raise RuntimeError("shader entry point has no #version directive")
    return "\n".join((lines[0], *(f"#define {name}" for name in defines), *lines[1:])) + "\n"


def layout_interface(text: str, qualifier: str) -> dict[int, tuple[str, str]]:
    interface: dict[int, tuple[str, str]] = {}
    for location, io, data_type, name in LAYOUT_IO_RE.findall(text):
        if io != qualifier or not location:
            continue
        index = int(location)
        value = (data_type, name)
        if index in interface and interface[index] != value:
            raise RuntimeError(f"duplicate layout location {index}: {interface[index]} vs {value}")
        interface[index] = value
    return interface


def minify_glsl(text: str) -> str:
    """Strip line comments/blank lines without rewriting GLSL directives."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    output: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            cleaned = line.rstrip()
        else:
            tokens = TOKEN_RE.findall(line.split("//", 1)[0])
            parts: list[str] = []
            for token in tokens:
                if parts and (
                    (WORD_RE.match(parts[-1]) and WORD_RE.match(token))
                    or (OPERATOR_RE.match(parts[-1]) and OPERATOR_RE.match(token))
                ):
                    parts.append(" ")
                parts.append(token)
            cleaned = "".join(parts)
        if cleaned.strip():
            output.append(cleaned)
    return "\n".join(output) + "\n"


def shader_bytes(text: str) -> int:
    return len(text.encode("utf-8"))
