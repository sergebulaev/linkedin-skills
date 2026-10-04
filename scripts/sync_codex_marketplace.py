#!/usr/bin/env python3
"""Refresh the nested Codex marketplace package from the repo root.

Codex marketplace entries must point at a plugin directory below the
marketplace root. Claude uses the repo root directly. This script keeps the
hidden Codex package in sync without changing the Claude-facing layout.
"""
from __future__ import annotations

import shutil
import subprocess
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


#: Files a user fills with their own material. The package must ship the blank
#: template and never a filled copy: syncing after filling one would stage a
#: voice fingerprint, client names and every number in a Story Bank into a
#: tracked file, which nothing in the credential scan would recognise.
PERSONAL = ("voice-profile.md", "story-bank.md")


def copy_path(src: Path, dest: Path) -> None:
    if src.is_dir():
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        if src.name == "references":
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", *PERSONAL)
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


def restore_templates(package_references: Path) -> list[str]:
    """Put the pristine templates back into the package from git.

    They are skipped by the copy above, so without this a fresh sync would leave
    the package without them entirely. Reading them from the index rather than
    from disk is the point: the working copy may be filled in.
    """
    restored = []
    for name in PERSONAL:
        tracked = f".codex-marketplace/linkedin-skills/references/{name}"
        # The blob is UTF-8. Decoding it with the locale (cp1252 on Windows) and
        # writing UTF-8 back turned every … and — into mojibake in the package.
        blob = subprocess.run(["git", "show", f"HEAD:{tracked}"],
                              cwd=ROOT, capture_output=True, encoding="utf-8")
        if blob.returncode == 0:
            (package_references / name).write_text(blob.stdout, encoding="utf-8")
            restored.append(name)
    return restored


def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    for rel in PATHS_TO_COPY:
        copy_path(ROOT / rel, DEST / rel)

    restored = restore_templates(DEST / "references")

    print(f"Synced Codex marketplace package: {DEST.relative_to(ROOT)}")
    if restored:
        print(f"  templates kept blank, not copied from the working tree: {', '.join(restored)}")


if __name__ == "__main__":
    main()
