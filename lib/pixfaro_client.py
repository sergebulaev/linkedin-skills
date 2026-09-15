"""Thin Pixfaro client for the LinkedIn Skills project.

Image layer (illustration generation). Sits alongside the read layer
(`apify_client`) and the write layer (`publora_client`) as the third
integration: generate an illustration, get back a hosted URL, and hand that
URL straight to Publora's `media_urls` when publishing.

Auth: PIXFARO_TOKEN env var (or constructor arg). Key format `pf_live_...`.
Without a token the skills fall back to "manual" mode: they draft the image
prompt and ask you to generate it yourself and paste the URL.

Endpoints (OpenAI-SDK-compatible):
  POST https://api.pixfaro.com/v1/images/generations
    body: {model, prompt, aspect_ratio "w:h", resolution "1K|2K|4K", overlay}
    overlay: {text|logo_id, position, opacity, font, color}  # pixel-exact
             composite, NOT model-generated text — so a cheap base model plus
             an overlay renders crisp feed images / thumbnails at low cost.
    resp: {id, url, cost, balance_after}   # hosted URL, not base64
  GET  /v1/key — "does this key work?": {key: {name, prefix, last4, scope},
    email_verified, balance?}. Any scope, free. THE way to verify a token —
    /v1/models is public and answers 200 to a wrong key.
  There is no /v1/render, /v1/templates/<id>, /v1/me, /v1/account or
  /v1/chat/completions — the endpoints on this page are the whole surface.
  POST /v1/renders — design templates (quote-card, post-card): typeset HTML,
    not a model generation, so text is always crisp. Same resp shape.
  GET  /v1/templates — live template catalog (public). Slots, sizes, price.
  POST /v1/logos — one-time brand-logo upload (PNG ≤1MB); the returned
    `logo_id` plugs into `overlay.logo_id`. Needs a FULL-scope key (a
    generate-scope key gets 403 insufficient_scope — upload in the dashboard
    instead).

Models (id / median latency / $ per image):
  gemini-flash-lite  3.0s   $0.041   (high-volume, cheap)
  nano-banana-2      10.7s  $0.080   (balanced default)
  gemini-pro-image   20.8s  $0.164   (premium, text-heavy)
  gpt-5-image        53.0s  $0.238   (max quality)

Caching: in-process LRU (128 entries, 6h TTL). Pass `force_refresh=True` to
bypass. Retries on transient 408/429/5xx (3 attempts, exponential backoff).
"""
from __future__ import annotations
import base64
import json
import os
import random
import time
from collections import OrderedDict
from typing import Any, Optional

import requests

from ._env import load_env


class PixfaroError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


BASE_URL = "https://api.pixfaro.com/v1"
DEFAULT_MODEL = "nano-banana-2"
KNOWN_MODELS = ("gemini-flash-lite", "nano-banana-2", "gemini-pro-image", "gpt-5-image")

RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}
CACHE_MAX_ENTRIES = 128
CACHE_TTL_SECONDS = 6 * 60 * 60

# Server-side logo constraints (mirrored so a bad upload fails fast + free):
# transparent PNG only, ≤1MB decoded, ≤2048px per side, ≤10 live per account.
MAX_LOGO_BYTES = 1_048_576


def _retry(attempts: int = 3, base_delay: float = 0.6):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except PixfaroError as e:
                    # Retryable = transient HTTP status OR a network-level failure
                    # (timeout/reset), both flagged on the exception at raise time.
                    if not getattr(e, "retryable", False) or attempt == attempts - 1:
                        raise
                    last_exc = e
                    time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.3))
            if last_exc:
                raise last_exc
        return wrapper
    return decorator


class PixfaroClient:
    """One method that matters: `generate`. Returns the hosted image URL."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 90.0):
        load_env()
        self.api_key = api_key or os.getenv("PIXFARO_TOKEN") or os.getenv("PIXFARO_API_KEY")
        if not self.api_key:
            raise PixfaroError(
                "No Pixfaro API key. Set PIXFARO_TOKEN (pf_live_...) or pass api_key. "
                "Sign up at https://pixfaro.com/signup?ref=linkedin-skills."
            )
        self.timeout = timeout
        self._session = requests.Session()
        self._cache: "OrderedDict[str, tuple[float, dict]]" = OrderedDict()

    # ---- cache helpers (mirror apify_client) ----
    def _cache_get(self, key: str) -> Optional[dict]:
        hit = self._cache.get(key)
        if not hit:
            return None
        ts, val = hit
        if time.time() - ts > CACHE_TTL_SECONDS:
            self._cache.pop(key, None)
            return None
        self._cache.move_to_end(key)
        return val

    def _cache_put(self, key: str, val: dict) -> None:
        self._cache[key] = (time.time(), val)
        self._cache.move_to_end(key)
        while len(self._cache) > CACHE_MAX_ENTRIES:
            self._cache.popitem(last=False)

    @_retry()
    def generate(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        aspect_ratio: str = "1:1",
        resolution: str = "1K",
        overlay: Optional[dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Generate one illustration. Returns {id, url, cost, balance_after}.

        `overlay` is passed through verbatim (e.g.
        {"text": "@handle", "position": "bottom-right", "opacity": 0.9,
         "color": "#0A66C2"}). Feed brand fields from the Voice & Brand Profile
        so every asset carries a consistent handle/logo/color.
        """
        if not prompt or not prompt.strip():
            raise PixfaroError("prompt cannot be empty")
        if len(prompt) > 4000:
            raise PixfaroError("prompt exceeds 4000 characters")

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if overlay:
            payload["overlay"] = overlay

        key = json.dumps(payload, sort_keys=True)
        if not force_refresh:
            cached = self._cache_get(key)
            if cached is not None:
                return cached

        data = self._post("/images/generations", payload)
        self._cache_put(key, data)
        return data

    @_retry()
    def edit(
        self,
        image_id: str,
        instruction: str,
        *,
        model: str = DEFAULT_MODEL,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        overlay: Optional[dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Iteratively edit a prior generation. Returns {id, url, cost, ...}.

        `image_id` must be the `img_...` id returned by a previous `generate`
        (or `edit`) call - hosted URLs are NOT accepted as the source. Omitting
        `aspect_ratio` keeps the source shape; omitting `resolution` inherits
        (and bills at) the source tier. Cheaper and more consistent than
        regenerating from scratch when the user wants "make the sky darker".
        """
        if not image_id or not str(image_id).startswith("img_"):
            raise PixfaroError(
                "edit requires a source image id (img_...) from a prior "
                "generation; hosted URLs are not accepted"
            )
        if not instruction or not instruction.strip():
            raise PixfaroError("instruction cannot be empty")
        if len(instruction) > 4000:
            raise PixfaroError("instruction exceeds 4000 characters")

        payload: dict[str, Any] = {
            "model": model,
            "image": image_id,
            "instruction": instruction,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        if overlay:
            payload["overlay"] = overlay

        key = "edit:" + json.dumps(payload, sort_keys=True)
        if not force_refresh:
            cached = self._cache_get(key)
            if cached is not None:
                return cached

        data = self._post("/images/edits", payload)
        self._cache_put(key, data)
        return data

    @_retry()
    def whoami(self) -> dict[str, Any]:
        """GET /v1/key — verify the configured key (any scope, free).

        Returns {key: {name, prefix, last4, scope, created_at}, email_verified,
        balance?} — `balance` only for full-scope keys. A wrong or truncated
        key raises PixfaroError(status_code=401) with Pixfaro's own message
        ("shown once at creation: copy it fully, or mint a new one")."""
        url = f"{BASE_URL}/key"
        try:
            r = self._session.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise PixfaroError(f"request failed: {e}", retryable=True) from e
        return self._handle(r)

    @_retry()
    def list_models(self) -> list[dict[str, Any]]:
        """GET /v1/models — live model catalog + per-tier pricing."""
        url = f"{BASE_URL}/models"
        try:
            r = self._session.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise PixfaroError(f"request failed: {e}", retryable=True) from e
        out = self._handle(r)
        return out.get("data", out) if isinstance(out, dict) else out

    @_retry()
    def list_templates(self) -> list[dict[str, Any]]:
        """GET /v1/templates — live design-template catalog.

        Each entry: {id, name, best_for, sizes, slots: [{name, type, required,
        max?, hint}], styles, price}. Public (no billing), so safe to call
        before offering a card to the user.
        """
        out = self._get("/templates")
        return out.get("templates", out) if isinstance(out, dict) else out

    @_retry()
    def render(
        self,
        template: str,
        slots: dict[str, Any],
        *,
        size: Optional[str] = None,
        scale: Optional[int] = None,
        style: Optional[Any] = None,
        overlay: Optional[Any] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """POST /v1/renders — typeset a design template to a hosted PNG.

        A render is billed and returned exactly like a generation
        ({id, url, cost, balance_after}) but the text is HTML-typeset, never
        model-drawn — a quote-card headline comes out crisp every time.

        Args:
            template: Template id from `list_templates` (e.g. "quote-card").
            slots: Slot values, e.g. {"quote": "...", "handle": "@me",
                "avatar": "default"}. Text slots for name/handle also accept
                "default" to pull from the account's brand identity.
            size: One of the template's size ids (e.g. "1:1", "4:5", "16:9",
                "og"); server default when omitted.
            scale: Raster density 1|2|3 (default 2; 3 bills a small surcharge).
            style: "auto" (rotates looks), "brand" (account palette), or an
                explicit {palette, font, layout, shadow} dict.
            overlay: Same corner-overlay contract as `generate`, or "default"
                for the account's saved brand kit.
        """
        if not template or not str(template).strip():
            raise PixfaroError("template id cannot be empty — see list_templates()")
        if not isinstance(slots, dict) or not slots:
            raise PixfaroError("slots must be a non-empty dict of slot values")

        payload: dict[str, Any] = {"template": template, "slots": slots}
        if size:
            payload["size"] = size
        if scale is not None:
            payload["scale"] = scale
        if style is not None:
            payload["style"] = style
        if overlay is not None:
            payload["overlay"] = overlay

        key = "render:" + json.dumps(payload, sort_keys=True)
        if not force_refresh:
            cached = self._cache_get(key)
            if cached is not None:
                return cached

        data = self._post("/renders", payload)
        self._cache_put(key, data)
        return data

    def upload_logo(self, path: str, *, name: Optional[str] = None) -> dict[str, Any]:
        """POST /v1/logos — one-time brand-logo upload.

        Returns {id: "logo_...", name, width, height, ...}. Save the id in the
        Voice & Brand Profile §6; from then on every `overlay` can carry
        `logo_id` instead of text. Constraints (checked server-side too):
        transparent PNG, ≤1MB, ≤2048px per side, ≤10 logos per account.

        Needs a FULL-scope key: a generate-scope key gets HTTP 403
        (insufficient_scope) — upload once in the dashboard instead.

        Deliberately NOT retried: a retry racing a slow success would store a
        duplicate and burn one of the 10 logo slots.
        """
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as e:
            raise PixfaroError(f"cannot read logo file: {e}") from e
        if not raw:
            raise PixfaroError("logo file is empty")
        if len(raw) > MAX_LOGO_BYTES:
            raise PixfaroError("logo must be ≤ 1 MB — export a smaller PNG")
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise PixfaroError("logo must be a transparent PNG (the file is not a PNG)")

        payload: dict[str, Any] = {"image": base64.b64encode(raw).decode("ascii")}
        if name:
            payload["name"] = name
        return self._post("/logos", payload)

    @_retry()
    def list_logos(self) -> list[dict[str, Any]]:
        """GET /v1/logos — this account's uploaded logos (full-scope key)."""
        out = self._get("/logos")
        return out.get("logos", out) if isinstance(out, dict) else out

    # ---- internals ----
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            r = self._session.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise PixfaroError(f"request failed: {e}", retryable=True) from e
        return self._handle(r)

    def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            r = self._session.post(url, json=json_body, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise PixfaroError(f"request failed: {e}", retryable=True) from e
        return self._handle(r)

    @staticmethod
    def _handle(r: requests.Response) -> dict[str, Any]:
        if r.status_code >= 400:
            detail = ""
            try:
                detail = json.dumps(r.json())
            except Exception:
                detail = r.text[:300]
            raise PixfaroError(
                f"HTTP {r.status_code}: {detail}",
                status_code=r.status_code,
                retryable=r.status_code in RETRYABLE_STATUSES,
            )
        try:
            return r.json()
        except ValueError as e:
            raise PixfaroError(f"non-JSON response: {r.text[:300]}") from e
