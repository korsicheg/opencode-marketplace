#!/usr/bin/env python3
"""Generate and validate the opencode remote skill index.

opencode fetches `<base>/index.json`, then downloads `<base>/<name>/<file>` for
every path listed in a skill's `files` array. It caches each skill alongside a
`.opencode-version` stamp and only re-downloads when `version` changes, so the
version must be derived from the skill's contents -- never from a repo-wide
commit sha, which would re-download every skill on every push.

Usage:
    build_index.py --out _site/skills     # validate, copy tree, write index.json
    build_index.py --check                # validate only, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

SKILL_ENTRYPOINT = "SKILL.md"
INDEX_FILENAME = "index.json"

# 48 bits of a content digest. Each version is only ever compared against the
# previous version of the same skill, so this leaves ample collision margin.
VERSION_LENGTH = 12

# opencode derives a skill's id from its directory name; this is the documented
# shape for it.
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# A path segment that parses as a URL would be resolved against the wrong base,
# so opencode rejects it. Mirrors `URL.canParse` closely enough for real paths.
URL_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")

WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:")

# Editor and OS droppings that must never reach the published index.
EXCLUDED_NAMES = frozenset({".DS_Store", "Thumbs.db", ".opencode-version"})
EXCLUDED_SUFFIXES = frozenset({".swp", ".swo", ".orig", ".rej"})


class ValidationError(Exception):
    """A single skill cannot be published as-is."""


class BuildFailed(Exception):
    """One or more skills failed validation; carries every reason at once."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("\n".join(reasons))
        self.reasons = reasons


class SkillEntry(NamedTuple):
    """One skill as it appears in index.json."""

    name: str
    version: str
    files: list[str]


class SkillIndex(NamedTuple):
    entries: list[SkillEntry]

    def as_json(self) -> str:
        payload = {"skills": [entry._asdict() for entry in self.entries]}
        return json.dumps(payload, indent=2) + "\n"


class Publication(NamedTuple):
    """Everything needed to lay the publishable tree out on disk."""

    index: SkillIndex
    skills_root: Path
    out_dir: Path

    def write(self) -> None:
        self._reset_output()
        self._copy_skills()
        self._write_index()

    def _reset_output(self) -> None:
        if self.out_dir.exists():
            shutil.rmtree(self.out_dir)
        self.out_dir.mkdir(parents=True)

    def _copy_skills(self) -> None:
        for entry in self.index.entries:
            for relative_path in entry.files:
                destination = self.out_dir / entry.name / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.skills_root / entry.name / relative_path, destination)

    def _write_index(self) -> None:
        (self.out_dir / INDEX_FILENAME).write_text(self.index.as_json(), encoding="utf-8")


def is_publishable(path: Path) -> bool:
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return not path.name.startswith("._")


def reject_invalid_name(name: str) -> None:
    if not NAME_PATTERN.match(name):
        raise ValidationError(f"directory name {name!r} is not lowercase-hyphenated")


def reject_unfetchable_path(relative_path: str) -> None:
    """Reject anything opencode's downloader would refuse.

    opencode drops the whole skill when a single entry in `files` fails this
    check, so one bad path costs every file in the skill.
    """
    if not relative_path:
        raise ValidationError("empty file path")
    for forbidden in ("\\", "\0", "?", "#"):
        if forbidden in relative_path:
            raise ValidationError(f"{relative_path!r} contains {forbidden!r}")
    if relative_path.startswith("/") or WINDOWS_ABSOLUTE_PATTERN.match(relative_path):
        raise ValidationError(f"{relative_path!r} is an absolute path")
    if URL_SCHEME_PATTERN.match(relative_path):
        raise ValidationError(f"{relative_path!r} parses as a URL")
    for segment in relative_path.split("/"):
        if not segment or segment in (".", ".."):
            raise ValidationError(f"{relative_path!r} has an invalid segment {segment!r}")


def reject_unpublishable_files(relative_paths: list[str]) -> None:
    for relative_path in relative_paths:
        reject_unfetchable_path(relative_path)
    if SKILL_ENTRYPOINT not in relative_paths:
        raise ValidationError(f"missing {SKILL_ENTRYPOINT}")


def discovered_files(skill_dir: Path) -> list[str]:
    return sorted(
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file() and is_publishable(path)
    )


def frontmatter_of(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValidationError(f"{SKILL_ENTRYPOINT} has no YAML frontmatter")
    _, _, remainder = text.partition("---")
    raw, separator, _ = remainder.partition("\n---")
    if not separator:
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not terminated")
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not valid YAML: {error}")
    if not isinstance(parsed, dict):
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not a mapping")
    return parsed


def reject_disagreeing_frontmatter(frontmatter: dict, name: str) -> None:
    declared = frontmatter.get("name")
    if declared is None:
        raise ValidationError("frontmatter is missing `name`")
    if declared != name:
        raise ValidationError(f"frontmatter name {declared!r} does not match directory {name!r}")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("frontmatter is missing a non-empty `description`")


def content_version(skill_dir: Path, relative_paths: list[str]) -> str:
    """Hash this skill's own contents, so an edit to one skill updates only it."""
    digest = hashlib.sha256()
    for relative_path in relative_paths:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update((skill_dir / relative_path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:VERSION_LENGTH]


def entry_for(skill_dir: Path) -> SkillEntry:
    reject_invalid_name(skill_dir.name)
    relative_paths = discovered_files(skill_dir)
    reject_unpublishable_files(relative_paths)
    reject_disagreeing_frontmatter(frontmatter_of(skill_dir / SKILL_ENTRYPOINT), skill_dir.name)
    return SkillEntry(
        name=skill_dir.name,
        version=content_version(skill_dir, relative_paths),
        files=relative_paths,
    )


def index_for(skills_root: Path) -> SkillIndex:
    """Validate every skill, reporting all failures rather than only the first."""
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_dirs:
        raise BuildFailed([f"no skill directories found under {skills_root}"])

    entries = []
    reasons = []
    for skill_dir in skill_dirs:
        try:
            entries.append(entry_for(skill_dir))
        except ValidationError as error:
            reasons.append(f"  {skill_dir.name}: {error}")

    if reasons:
        raise BuildFailed(reasons)
    return SkillIndex(entries)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "skills",
        help="directory holding one folder per skill (default: ./skills)",
    )
    parser.add_argument("--out", type=Path, help="directory to write the publishable tree into")
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    arguments = parser.parse_args()
    if not arguments.check and arguments.out is None:
        parser.error("either --out or --check is required")
    return arguments


def report(index: SkillIndex, verb: str) -> None:
    for entry in index.entries:
        print(f"{verb}  {entry.name}  {entry.version}  {len(entry.files)} files")


def main() -> int:
    arguments = parse_arguments()
    skills_root = arguments.skills.resolve()
    if not skills_root.is_dir():
        print(f"error: {skills_root} is not a directory", file=sys.stderr)
        return 1

    try:
        index = index_for(skills_root)
    except BuildFailed as failure:
        print(f"error: skills failed validation\n{failure}", file=sys.stderr)
        return 1

    if arguments.check:
        report(index, "ok")
        print(f"\n{len(index.entries)} skills validated")
        return 0

    out_dir = arguments.out.resolve()
    Publication(index, skills_root, out_dir).write()
    report(index, "published")
    print(f"\nwrote {out_dir / INDEX_FILENAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
