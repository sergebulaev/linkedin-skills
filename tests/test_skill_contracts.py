"""Every `lib.*` call a SKILL.md tells the agent to make must actually exist.

A SKILL.md is executable in practice: the agent reads the call and makes it. So a
renamed function or a dropped keyword argument is not a documentation lapse, it
is a runtime failure that nothing else in this repo notices - the markdown still
parses, the references still resolve, the imports still work.

Offline. No credentials, no network.
"""
from __future__ import annotations

import inspect
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# lib.foo( ... ) and lib.ApifyClient.foo( ... ), tolerating one nesting level of
# parentheses inside the arguments (kind="post", platforms=[{...}]).
CALL = re.compile(r"\blib\.(?:ApifyClient\(?\)?\.)?([a-z_]+)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)")
KEYWORD = re.compile(r"(?:^|,)\s*([a-z_][a-z0-9_]*)\s*=")


def documents() -> list[pathlib.Path]:
    docs = sorted(ROOT.joinpath("skills").rglob("*.md"))
    root_skill = ROOT / "SKILL.md"
    if root_skill.is_file():
        docs.append(root_skill)
    return docs


def documented_calls():
    """(document, function name, [keyword arguments]) for every documented call."""
    for document in documents():
        for match in CALL.finditer(document.read_text(encoding="utf-8")):
            yield document, match.group(1), KEYWORD.findall(match.group(2))


class SkillContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import lib
        from lib.apify_client import ApifyClient

        cls.lib = lib
        cls.client = ApifyClient
        cls.calls = list(documented_calls())

    def resolve(self, name):
        return getattr(self.lib, name, None) or getattr(self.client, name, None)

    def test_documentation_actually_calls_something(self):
        """Guards the regex itself: a rewrite that matches nothing would pass
        every other test in this file silently."""
        self.assertGreaterEqual(
            len({name for _, name, _ in self.calls}), 10,
            "found almost no lib.* calls in the skills - has the call syntax changed?",
        )

    def test_every_documented_function_exists(self):
        missing = sorted({
            f"{document.relative_to(ROOT)}: lib.{name}()"
            for document, name, _ in self.calls
            if not callable(self.resolve(name))
        })
        self.assertEqual(missing, [], "skills document calls that do not exist:\n  " + "\n  ".join(missing))

    def test_every_documented_keyword_is_accepted(self):
        problems = []
        for document, name, keywords in self.calls:
            function = self.resolve(name)
            if not callable(function):
                continue
            try:
                signature = inspect.signature(function)
            except (TypeError, ValueError):
                continue
            if any(p.kind is p.VAR_KEYWORD for p in signature.parameters.values()):
                continue                      # **kwargs accepts anything
            accepted = set(signature.parameters) - {"self"}
            for keyword in keywords:
                if keyword not in accepted:
                    problems.append(
                        f"{document.relative_to(ROOT)}: lib.{name}({keyword}=...) "
                        f"is not accepted; it takes {sorted(accepted)}"
                    )
        self.assertEqual(problems, [], "skills document arguments that do not exist:\n  " + "\n  ".join(problems))

    def test_the_keyword_check_can_fail(self):
        """The check above is only worth having if a wrong name trips it."""
        signature = inspect.signature(self.resolve("fetch_post_comments"))
        accepted = set(signature.parameters) - {"self"}
        self.assertNotIn("definitely_not_a_parameter", accepted)
        self.assertIn("sort_order", accepted, "sort_order went missing from fetch_post_comments")

    def test_skill_count_matches_the_manifest(self):
        import json

        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        promised = re.match(r"\s*(\d+)\b", manifest.get("description", ""))
        directories = [d for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file()]
        if promised:
            self.assertEqual(
                int(promised.group(1)), len(directories),
                "the manifest's skill count and the number of loadable skills disagree",
            )

    def test_every_skill_is_mirrored_for_claude_code(self):
        """`.claude/skills/<name>` is how Claude Code finds a plain clone. A
        missing symlink is silent: the skill simply never appears."""
        mirror = ROOT / ".claude" / "skills"
        if not mirror.is_dir():
            self.skipTest("no .claude/skills mirror in this checkout")
        skills = {d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file()}
        mirrored = {p.name for p in mirror.iterdir()}
        self.assertEqual(
            skills - mirrored, set(),
            "skills with no .claude/skills symlink, so a fresh clone will not see them",
        )


if __name__ == "__main__":
    unittest.main()
