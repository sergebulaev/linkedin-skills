"""Internal helper to load .env when python-dotenv is available."""
from __future__ import annotations

from pathlib import Path

_ENV_LOADED = False
_LOADED_PATHS: list[str] = []


def env_candidates() -> list[Path]:
    """Where `load_env` looks, in order: upward from the cwd, then the repo root
    (this file's parent's parent). Exposed so a "token set but not loaded"
    diagnosis can name the exact file it expected."""
    out: list[Path] = []
    try:
        from dotenv import find_dotenv

        found = find_dotenv(usecwd=True)
        if found:
            out.append(Path(found))
    except ImportError:
        cur = Path.cwd()
        for d in [cur, *cur.parents]:
            if (d / ".env").is_file():
                out.append(d / ".env")
                break
    root = Path(__file__).resolve().parents[1] / ".env"
    if root not in out:
        out.append(root)
    return out


def loaded_env_paths() -> list[str]:
    """The .env files `load_env` actually read (empty when python-dotenv is missing)."""
    return list(_LOADED_PATHS)


def find_unloaded_token_file(var_names=("PIXFARO_TOKEN", "PIXFARO_API_KEY")) -> str | None:
    """A .env in the expected places that DEFINES one of `var_names` while the
    variable is absent from the environment — the silent-manual-mode case
    (python-dotenv not installed, or the file was never loaded). Returns the
    path to name in the message, or None."""
    import os

    if any(os.getenv(v) for v in var_names):
        return None
    for path in env_candidates():
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    continue
                key, _, value = stripped.partition("=")
                if key.strip() in var_names and value.strip().strip("\"'"):
                    return str(path)
        except OSError:
            continue
    return None


def load_env(force: bool = False) -> None:
    """Load environment variables from .env if python-dotenv is installed.

    Safe no-op if python-dotenv is missing, preserving Tier 0 (manual)
    zero-dependency operation. Searches upwards from the current working
    directory and checks the repository root. Existing environment variables
    are preserved.
    """
    global _ENV_LOADED
    if _ENV_LOADED and not force:
        return

    try:
        from dotenv import find_dotenv, load_dotenv

        # 1. Search upwards from cwd (for plugin users working in project directories)
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
            _LOADED_PATHS.append(dotenv_path)

        # 2. Check repo root relative to this file
        repo_env = Path(__file__).resolve().parents[1] / ".env"
        if repo_env.is_file():
            load_dotenv(repo_env)
            _LOADED_PATHS.append(str(repo_env))
    except ImportError:
        pass

    _ENV_LOADED = True
