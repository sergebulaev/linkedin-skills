"""The one runnable tool inside the skills, which had no tests at all.

`skills/linkedin-humanizer/scripts/test_detectors.py` runs a draft past several
AI detectors and reports how far apart they land. Its point is the spread, not
any single score, so the part that carries the argument is `verdict_for_spread`
and the report it builds around it. All of that is pure and offline.

The name is unfortunate — it is a tool, not a test suite — but it is cited by
three documents and renaming it is a public-surface change for no gain here.

Offline. `--demo` exists precisely so no key and no paid call is needed.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import sys
import unittest

TOOL = pathlib.Path(__file__).resolve().parent.parent / \
    "skills" / "linkedin-humanizer" / "scripts" / "test_detectors.py"


def load_tool():
    """The tool lives outside any package, so it is loaded by path.

    It has to be registered in sys.modules before executing: @dataclass resolves
    its own module through sys.modules and fails on a module that is not there.
    """
    spec = importlib.util.spec_from_file_location("detector_tool", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = load_tool()


class SpreadVerdict(unittest.TestCase):
    """The scale the whole tool exists to deliver."""

    def test_the_bands_are_contiguous_and_ordered(self):
        """A gap or an overlap here would make a spread land in the wrong band,
        which is the one number the user is asked to act on."""
        labels = [tool.verdict_for_spread(float(s))[0] for s in range(0, 101)]
        self.assertEqual(labels[0], "CONSENSUS")
        self.assertEqual(labels[100], "USELESS")
        changes = [(s, labels[s - 1], labels[s]) for s in range(1, 101) if labels[s] != labels[s - 1]]
        self.assertEqual([(16, "CONSENSUS", "MIXED"),
                          (31, "MIXED", "DIVERGENT"),
                          (51, "DIVERGENT", "USELESS")], changes)

    def test_each_boundary_falls_on_the_lower_band(self):
        for spread, expected in ((15, "CONSENSUS"), (30, "MIXED"), (50, "DIVERGENT")):
            with self.subTest(spread=spread):
                self.assertEqual(tool.verdict_for_spread(float(spread))[0], expected)

    def test_every_verdict_explains_itself(self):
        """The label alone invites over-reading. The sentence beside it is what
        stops a CONSENSUS being quoted as proof."""
        for spread in (0, 20, 40, 90):
            label, plain = tool.verdict_for_spread(float(spread))
            self.assertTrue(plain and plain[0].islower(), f"{label}: {plain!r}")
            self.assertGreater(len(plain), 20, f"{label} has no real explanation")

    def test_consensus_still_refuses_to_claim_proof(self):
        """The tool's entire premise is that detectors are not evidence, and the
        tightest band is where that is easiest to forget."""
        _, plain = tool.verdict_for_spread(0.0)
        self.assertIn("not proof", plain)


class DemoMode(unittest.TestCase):
    """Canned scores, so the tool is usable and testable with no keys."""

    def test_it_returns_one_result_per_detector(self):
        results = tool.run_demo("a draft")
        self.assertEqual(len(results), len(tool._DEMO_DETECTORS))
        self.assertEqual([r.name for r in results], list(tool._DEMO_DETECTORS))

    def test_the_same_text_always_scores_the_same(self):
        """Derived from a hash on purpose: a demo that shifted between runs
        would look like the detectors moved."""
        first = [r.score for r in tool.run_demo("identical text")]
        second = [r.score for r in tool.run_demo("identical text")]
        self.assertEqual(first, second)

    def test_different_text_scores_differently(self):
        self.assertNotEqual([r.score for r in tool.run_demo("one")],
                            [r.score for r in tool.run_demo("another")])

    def test_scores_stay_inside_the_percentage_range(self):
        for result in tool.run_demo("whatever"):
            self.assertGreaterEqual(result.score, 0.0)
            self.assertLessEqual(result.score, 100.0)


class Report(unittest.TestCase):
    def setUp(self):
        # render_report both returns the report and prints it; the printing is
        # the tool's user interface and not what is under test here.
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            self.report = tool.render_report("a draft to check", tool.run_demo("a draft to check"))
        self.printed = printed.getvalue()

    def test_the_report_leads_with_the_spread(self):
        self.assertIn("spread", self.report)
        self.assertIn("verdict", self.report)

    def test_the_spread_is_the_actual_range_of_the_scores(self):
        scores = [r.score for r in tool.run_demo("a draft to check")]
        self.assertAlmostEqual(self.report["spread"], max(scores) - min(scores), places=6)

    def test_the_verdict_matches_the_spread(self):
        self.assertEqual(self.report["verdict"], tool.verdict_for_spread(self.report["spread"])[0])

    def test_every_detector_is_represented(self):
        self.assertEqual(len(self.report["scores"]), len(tool._DEMO_DETECTORS))

    def test_what_it_prints_leads_with_the_disagreement(self):
        """The printed block is what a user actually reads, and the headline has
        to be the spread rather than any one detector's number."""
        self.assertIn("Spread", self.printed)
        self.assertIn(self.report["verdict"], self.printed)
        self.assertIn(self.report["translation"], self.printed)


class ApiDetectorsAreNotCalled(unittest.TestCase):
    """Guards the boundary: nothing in this file may reach a paid endpoint."""

    def test_demo_mode_touches_no_detector_function(self):
        called = []
        originals = list(tool.API_DETECTORS)
        tool.API_DETECTORS[:] = [lambda text, c=called: c.append(text)]
        try:
            tool.run_demo("text")
        finally:
            tool.API_DETECTORS[:] = originals
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
