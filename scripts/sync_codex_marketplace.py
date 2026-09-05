#!/usr/bin/env python3
"""Refresh the nested Codex marketplace package from the repo root.

Codex marketplace entries must point at a plugin directory below the
marketplace root. Claude uses the repo root directly. This script keeps the
hidden Codex package in sync without changing the Claude-facing layout.
"""
from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".codex-marketplace" / "linkedin-skills"

PATHS_TO_COPY = [
    ".codex-plugin",
    ".codexignore",
    "SKILL.md",
    "README.md",
    "SECURITY.md",
    "skills",
    "references",
    "lib",
    "scripts",
    "assets",
    "requirements.txt",
    "requirements-lock.txt",
    ".env.example",
    "LICENSE",
]


def copy_path(src: Path, dest: Path) -> None:
    if src.is_dir():
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        if src.name == "scripts":
            ignore = shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "check_markdown_references.py",
                "sync_codex_marketplace.py",
            )
        shutil.copytree(src, dest, ignore=ignore)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    for rel in PATHS_TO_COPY:
        copy_path(ROOT / rel, DEST / rel)

    print(f"Synced Codex marketplace package: {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
