"""The instructions are the product; this checks the parts of them a machine can.

7,000-odd lines of markdown do the actual work here, and almost none of it can
be unit tested — whether a hook formula is any good is not a matter of fact. But
plenty of it rots in ways that are: a skill renamed and a sibling still pointing
at the old name, a Files list naming something deleted, a formula cited by a
number nobody defined, a platform limit LinkedIn has since changed.

None of that shows up in a diff review, and all of it reaches the agent as
instructions it will follow.

Offline. No credentials, no network: platform limits come from a recorded
fixture, so a drift here means our docs moved, not that LinkedIn did.
"""
from __future__ import annotations

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
SKILLS = sorted(d for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file())
NAMES = {d.name for d in SKILLS}


def markdown(directory: pathlib.Path):
    return sorted(directory.rglob("*.md"))


def frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    import yaml                                   # maintainer tooling only

    return yaml.safe_load(text.split("---", 2)[1]) or {}


class CrossReferences(unittest.TestCase):
    def test_every_sibling_named_is_a_real_skill(self):
        """Renaming a skill is a public-surface change; a stale mention sends
        the agent to a skill that does not exist."""
        dangling = {}
        for skill in SKILLS:
            for document in markdown(skill):
                for match in re.finditer(r"`(linkedin-[a-z][a-z-]*)`", document.read_text(encoding="utf-8")):
                    name = match.group(1)
                    if name not in NAMES and name != "linkedin-skills":
                        dangling.setdefault(name, set()).add(str(document.relative_to(ROOT)))
        self.assertEqual(dangling, {}, f"skills referenced that do not exist: { {k: sorted(v) for k, v in dangling.items()} }")

    def test_the_check_would_notice_a_rename(self):
        self.assertIn("linkedin-humanizer", NAMES)
        self.assertNotIn("linkedin-nonexistent", NAMES)

    def test_files_sections_list_files_that_exist(self):
        missing = []
        for skill in SKILLS:
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            section = re.search(r"^## Files\n(.*?)(?=\n## |\Z)", text, re.S | re.M)
            if not section:
                continue
            for line in section.group(1).splitlines():
                entry = re.match(r"\s*-\s*`([^`]+)`", line)
                if entry and not entry.group(1).startswith(("http", "lib.")):
                    if not (skill / entry.group(1)).exists():
                        missing.append(f"{skill.name}: {entry.group(1)}")
        self.assertEqual(missing, [], "Files sections name things that are not there:\n  " + "\n  ".join(missing))


class HookFormulas(unittest.TestCase):
    """`references/hook-formulas.md` is cited by number from several skills."""

    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "references" / "hook-formulas.md").read_text(encoding="utf-8")
        cls.defined = {m.group(1) for m in re.finditer(r"^## (F\d+) ", cls.source, re.M)}

    def test_the_count_in_the_title_is_the_count_on_the_page(self):
        promised = re.search(r"^# (\d+) ", self.source, re.M)
        self.assertIsNotNone(promised, "the file no longer states how many formulas it holds")
        self.assertEqual(int(promised.group(1)), len(self.defined),
                         f"the title promises {promised.group(1)}, the page defines {len(self.defined)}")

    def test_the_numbering_has_no_gaps(self):
        numbers = sorted(int(name[1:]) for name in self.defined)
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)),
                         f"formula numbering is not contiguous: {numbers}")

    def test_no_skill_cites_a_formula_that_does_not_exist(self):
        cited = set()
        for document in markdown(ROOT / "skills") + markdown(ROOT / "references"):
            if document.name == "hook-formulas.md":
                continue
            cited |= set(re.findall(r"\b(F\d{1,2})\b", document.read_text(encoding="utf-8")))
        self.assertEqual(sorted(cited - self.defined), [], "formulas cited but never defined")


class PlatformLimits(unittest.TestCase):
    """What the skills tell the agent about LinkedIn, against what Publora
    reports. A stale number here produces posts the API rejects."""

    @classmethod
    def setUpClass(cls):
        cls.limits = json.loads((FIXTURES / "publora_platform_limits.json").read_text())["linkedin"]

    def test_the_post_character_cap_matches(self):
        cap = self.limits["characters"]["standard"]
        self.assertEqual(cap, 3000, "the fixture itself changed; re-check the skills before updating it")
        quoted = set()
        for document in markdown(ROOT / "skills") + [ROOT / "SKILL.md"]:
            text = document.read_text(encoding="utf-8")
            quoted |= {int(n.replace(",", "")) for n in
                       re.findall(r"([\d,]{3,6})\s*(?:char|characters)\b", text)}
        over = sorted(n for n in quoted if n > cap)
        self.assertEqual(over, [], f"skills quote character counts above LinkedIn's {cap}: {over}")

    def test_the_image_count_ceiling_is_not_overstated(self):
        """linkedin-post-writer offers multi-image grids; the ceiling is 10."""
        ceiling = self.limits["images"]["maxCount"]
        text = (ROOT / "skills" / "linkedin-post-writer" / "SKILL.md").read_text(encoding="utf-8")
        for low, high in re.findall(r"\((\d+)-(\d+) images", text):
            self.assertLessEqual(int(high), ceiling,
                                 f"offers up to {high} images, LinkedIn accepts {ceiling}")


class SkillConventions(unittest.TestCase):
    """The rules CLAUDE.md calls mandatory, checked rather than trusted."""

    def test_every_description_is_within_the_hard_limit(self):
        too_long = []
        for skill in SKILLS:
            description = (frontmatter(skill / "SKILL.md").get("description") or "")
            if len(description) > 510:
                too_long.append(f"{skill.name}: {len(description)} chars")
        self.assertEqual(too_long, [], "descriptions past the 510-char hard limit:\n  " + "\n  ".join(too_long))

    def test_no_description_uses_an_em_dash(self):
        offenders = [s.name for s in SKILLS
                     if re.search(r"[—–]", frontmatter(s / "SKILL.md").get("description") or "")]
        self.assertEqual(offenders, [], "em dashes are not allowed in description fields")

    def test_every_description_says_what_it_is_not_for(self):
        """Two different jobs wear the same "Not for" phrasing, and both matter:
        steering away from an overlapping sibling ("Not for reviewing existing
        drafts (use linkedin-humanizer)"), and heading off a false expectation
        the skill cannot meet ("Not for beating AI detectors"). Requiring the
        clause without requiring a sibling keeps both honest."""
        missing = [s.name for s in SKILLS
                   if not re.search(r"\bnot\b", frontmatter(s / "SKILL.md").get("description") or "", re.I)]
        self.assertEqual(missing, [], "descriptions that never say what they are not for:\n  " + "\n  ".join(missing))

    def test_any_sibling_a_description_points_at_is_real(self):
        """A sentinel aimed at a renamed skill is worse than none: it sends the
        agent somewhere that does not exist."""
        broken = []
        for skill in SKILLS:
            description = frontmatter(skill / "SKILL.md").get("description") or ""
            for named in re.findall(r"\(use (linkedin-[a-z-]+)", description):
                if named not in NAMES:
                    broken.append(f"{skill.name} -> {named}")
        self.assertEqual(broken, [], "sentinels pointing at skills that do not exist:\n  " + "\n  ".join(broken))

    def test_at_least_half_the_skills_steer_to_a_named_sibling(self):
        """Not every skill has a twin, but twelve skills in one bundle mostly do.
        If this ever drops, the sentinels are being written as boilerplate rather
        than as routing."""
        steering = sum(1 for s in SKILLS
                       if re.search(r"\(use linkedin-", frontmatter(s / "SKILL.md").get("description") or ""))
        self.assertGreaterEqual(steering, len(SKILLS) // 2,
                                f"only {steering} of {len(SKILLS)} descriptions route to a sibling")

    def test_skills_that_read_other_peoples_text_carry_the_untrusted_rule(self):
        """Anything reading the Apify layer handles text strangers wrote. The
        data-is-not-instructions rule has to travel with it."""
        missing = []
        for skill in SKILLS:
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            reads = re.search(r"fetch_post|fetch_post_comments|fetch_user_recent_comments|fetch_post_engagers", text)
            if reads and "Untrusted content" not in text:
                missing.append(skill.name)
        self.assertEqual(missing, [], "reads fetched text without the untrusted-content section:\n  " + "\n  ".join(missing))

    def test_skill_local_hard_rules_defer_to_the_global_voice_rules(self):
        missing = []
        for skill in SKILLS:
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            if "## Hard rules" in text and "Global voice rules" not in text:
                missing.append(skill.name)
        self.assertEqual(missing, [], "Hard rules that do not point at the global voice rules:\n  " + "\n  ".join(missing))


if __name__ == "__main__":
    unittest.main()


class EnvironmentVariableNames(unittest.TestCase):
    """The names the code reads must be the names the docs tell people to set.

    `scripts/selftest.py` asked for `PUBLORA_PLATFORM_ID` while every other file
    reads `LINKEDIN_PLATFORM_ID`, so its setup hint named a variable that does
    nothing. Nothing caught it: the live test passed the invented name on the
    command line and read it back, a closed loop that proved only itself.
    """

    #: Every credential the bundle reads. Adding one means adding it here.
    KNOWN = {
        "APIFY_TOKEN", "PUBLORA_API_KEY", "LINKEDIN_PLATFORM_ID",
        "PIXFARO_TOKEN", "PIXFARO_API_KEY", "LINKEDIN_SKILLS_CUSTOM_POSTER",
    }

    def read_by_code(self):
        found = set()
        for source in list((ROOT / "lib").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")):
            text = source.read_text(encoding="utf-8")
            found |= set(re.findall(r'getenv\(\s*["\']([A-Z][A-Z0-9_]+)["\']', text))
            found |= set(re.findall(r'environ\[\s*["\']([A-Z][A-Z0-9_]+)["\']', text))
        return {name for name in found
                if any(k in name for k in ("APIFY", "PUBLORA", "PIXFARO", "LINKEDIN"))}

    def test_no_credential_name_is_invented(self):
        unknown = sorted(self.read_by_code() - self.KNOWN)
        self.assertEqual(unknown, [],
                         "code reads variables that are not part of the bundle's contract; "
                         "either a typo or an undocumented new one")

    def test_the_platform_id_has_exactly_one_name(self):
        names = {n for n in self.read_by_code() if "PLATFORM_ID" in n}
        self.assertEqual(names, {"LINKEDIN_PLATFORM_ID"},
                         f"two names for the same setting: {sorted(names)}")

    def test_env_example_documents_what_the_code_reads(self):
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        documented = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", example, re.M))
        # The custom-poster hook is a power-user escape hatch, not a credential.
        required = self.read_by_code() - {"LINKEDIN_SKILLS_CUSTOM_POSTER", "PIXFARO_API_KEY"}
        missing = sorted(required - documented)
        self.assertEqual(missing, [], f".env.example never mentions: {missing}")
