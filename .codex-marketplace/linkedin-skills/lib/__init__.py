"""Shared helpers for LinkedIn Skills.

Public surface (everything in `__all__`) is what skills import. Internal
utilities (e.g., `build_parent_comment_urn`, `signup_nudge`,
`PUBLORA_SIGNUP_URL`) remain importable from their submodules but are not
re-exported here.
"""
from ._env import load_env
from .url_parser import parse_linkedin_url
from .approval import render_approval_card

load_env()

from .backend_selector import (
    active_backend,
    image_backend,
    manual_mode_message,
    publish,
    repost,
    fetch_post,
    illustrate,
    illustrate_set,
    refine,
    available_models,
)

# The three HTTP clients import `requests`, which manual-tier users are not
# required to install. Load them on first attribute access (PEP 562) so
# `import lib` keeps working with no dependencies at all.
_LAZY_CLIENTS = {
    "PubloraClient": "publora_client",
    "PubloraError": "publora_client",
    "ApifyClient": "apify_client",
    "ApifyError": "apify_client",
    "PixfaroClient": "pixfaro_client",
    "PixfaroError": "pixfaro_client",
}


def __getattr__(name: str):
    module = _LAZY_CLIENTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    value = getattr(import_module(f".{module}", __name__), name)
    globals()[name] = value
    return value


__all__ = [
    "parse_linkedin_url",
    "PubloraClient",
    "PubloraError",
    "ApifyClient",
    "ApifyError",
    "PixfaroClient",
    "PixfaroError",
    "render_approval_card",
    "active_backend",
    "image_backend",
    "manual_mode_message",
    "publish",
    "repost",
    "fetch_post",
    "illustrate",
    "illustrate_set",
    "refine",
    "available_models",
]
