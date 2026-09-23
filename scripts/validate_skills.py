#!/usr/bin/env python3
"""Validate every skill under skills/ against what opencode v2 needs to load it.

opencode derives a skill's id from its directory and offers it to the model by
its `description`, so a malformed skill does not fail loudly there -- it is
silently misnamed or never offered. This check makes that failure visible
before it is merged. Every failure is reported at once, not only the first.

Usage:
    validate_skills.py [--skills DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SKILL_ENTRYPOINT = "SKILL.md"
FRONTMATTER_DELIMITER = "---"

# opencode v2's documented shape for a skill id, which it takes from the
# directory name.
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_MAX_LENGTH = 64


class ValidationError(Exception):
    """A single skill cannot be loaded as intended."""


def reject_invalid_id(skill_id: str) -> None:
    if not ID_PATTERN.match(skill_id):
        raise ValidationError(f"directory name {skill_id!r} is not lowercase-hyphenated")
    if len(skill_id) > ID_MAX_LENGTH:
        raise ValidationError(f"directory name {skill_id!r} exceeds {ID_MAX_LENGTH} characters")


def frontmatter_of(skill_md: Path) -> dict:
    if not skill_md.is_file():
        raise ValidationError(f"missing {SKILL_ENTRYPOINT}")
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith(FRONTMATTER_DELIMITER):
        raise ValidationError(f"{SKILL_ENTRYPOINT} has no YAML frontmatter")
    raw, separator, _ = text[len(FRONTMATTER_DELIMITER):].partition(f"\n{FRONTMATTER_DELIMITER}")
    if not separator:
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not terminated")
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not valid YAML: {error}")
    if not isinstance(parsed, dict):
        raise ValidationError(f"{SKILL_ENTRYPOINT} frontmatter is not a mapping")
    return parsed


def reject_incomplete_frontmatter(frontmatter: dict, skill_id: str) -> None:
    # `name` is an optional display name in v2; when present it must not
    # disagree with the id the model actually calls the skill by.
    declared = frontmatter.get("name", skill_id)
    if declared != skill_id:
        raise ValidationError(f"frontmatter name {declared!r} does not match directory {skill_id!r}")

    # Without a description v2 never offers the skill to the model.
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("frontmatter is missing a non-empty `description`")


def validate_skill(skill_dir: Path) -> None:
    reject_invalid_id(skill_dir.name)
    frontmatter = frontmatter_of(skill_dir / SKILL_ENTRYPOINT)
    reject_incomplete_frontmatter(frontmatter, skill_dir.name)


def failures_in(skill_dirs: list[Path]) -> list[str]:
    failures = []
    for skill_dir in skill_dirs:
        try:
            validate_skill(skill_dir)
        except ValidationError as error:
            failures.append(f"  {skill_dir.name}: {error}")
    return failures


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "skills",
        help="directory holding one folder per skill (default: ./skills)",
    )
    return parser.parse_args()


def main() -> int:
    skills_root = parse_arguments().skills.resolve()
    if not skills_root.is_dir():
        print(f"error: {skills_root} is not a directory", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_dirs:
        print(f"error: no skill directories found under {skills_root}", file=sys.stderr)
        return 1

    failures = failures_in(skill_dirs)
    if failures:
        print("error: skills failed validation", *failures, sep="\n", file=sys.stderr)
        return 1

    print(f"{len(skill_dirs)} skills validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
