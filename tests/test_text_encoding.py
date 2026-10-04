"""Text I/O states its encoding, so the bundle behaves the same on Windows.

Python's default text encoding is the locale's. On Linux and macOS that is
UTF-8, so a `read_text()` without `encoding=` works there and nobody notices. On
Windows it is the ANSI code page (cp1252 on most installs): the same call
misreads the em dashes and curly quotes this bundle's markdown is full of, or
fails outright on a byte cp1252 does not define. Pipes default to it as well,
and cp1252 cannot encode the emoji in the approval messages at all.

The first test is static, so the Linux CI run catches a new unencoded call. The
other two give a child process cp1252 pipes through PYTHONIOENCODING, which
reproduces the Windows default on any OS. Subprocess pipes are not scanned: what
a child writes depends on the child (see `utf8_pipes` in scripts/selftest.py).

Offline. No credentials, no network.
"""
from __future__ import annotations

import ast
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "linkedin-humanizer" / "scripts" / "test_detectors.py"

# Dot-directories (.git, .claude, the generated .codex-marketplace), local
# scratch and virtualenvs are not this repo's source.
SKIP_DIRS = {"venv", "testing", "marketing", "node_modules"}
MODE_CHARS = set("rwxabt+")


def sources() -> list[pathlib.Path]:
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        found += [pathlib.Path(folder, name) for name in files if name.endswith(".py")]
    return sorted(found)


def unencoded_text_io(tree: ast.AST):
    """(line, call) for each text-mode open / read_text / write_text without `encoding=`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or any(k.arg == "encoding" for k in node.keywords):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in ("read_text", "write_text"):
            yield node.lineno, name
        elif name == "open":
            # open(path, mode) for the builtin, path.open(mode) for pathlib. An
            # attribute call whose first argument is not a mode (webbrowser.open,
            # Image.open) is something else and is left alone.
            builtin = isinstance(func, ast.Name)
            args = node.args[1:] if builtin else node.args
            mode = args[0] if args else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if mode is None:
                if builtin:
                    yield node.lineno, "open"
            elif isinstance(mode, ast.Constant) and isinstance(mode.value, str) \
                    and set(mode.value) <= MODE_CHARS and "b" not in mode.value:
                yield node.lineno, "open"


def run_with_cp1252_pipes(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                          capture_output=True, timeout=120, **kwargs)


class TextIOStatesItsEncoding(unittest.TestCase):

    def test_every_text_mode_file_call_names_an_encoding(self):
        offenders = [f"{path.relative_to(ROOT)}:{line} {call}()"
                     for path in sources()
                     for line, call in unencoded_text_io(ast.parse(path.read_text(encoding="utf-8")))]
        self.assertEqual(offenders, [], 'pass encoding="utf-8": Windows would read these as cp1252')

    def test_importing_lib_lets_a_cp1252_pipe_print_an_approval_message(self):
        code = ("import lib; print(lib.manual_mode_message("
                "'Fair point \\u2014 we saw the same', 'https://www.linkedin.com/posts/x'))")
        run = run_with_cp1252_pipes(["-c", code])
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace")[-300:])
        out = run.stdout.decode("utf-8")
        self.assertIn("✅", out)
        self.assertIn("Fair point — we saw the same", out)

    def test_detector_tool_reads_a_piped_draft_as_utf8_and_prints_its_emoji(self):
        draft = "We cut churn 14% in Q3 — here’s the one change that did it \U0001F680"
        piped = run_with_cp1252_pipes([str(TOOL), "--stdin", "--demo"], input=draft.encode("utf-8"))
        inline = run_with_cp1252_pipes([str(TOOL), "--text", draft, "--demo"])
        for run in (piped, inline):
            self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace")[-300:])
        # --demo derives its scores from a hash of the text, so a draft misread
        # on the way in scores differently from the same draft passed inline.
        self.assertEqual(piped.stdout, inline.stdout)
        self.assertIn("here’s the one change", piped.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
