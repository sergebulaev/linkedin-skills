"""Internal helper to load .env when python-dotenv is available."""
from __future__ import annotations

from pathlib import Path

_ENV_LOADED = False


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

        # 2. Check repo root relative to this file
        repo_env = Path(__file__).resolve().parents[1] / ".env"
        if repo_env.is_file():
            load_dotenv(repo_env)
    except ImportError:
        pass

    _ENV_LOADED = True
