#!/usr/bin/env python3
"""Check that every key we send an Apify actor exists in that actor's schema.

Apify does not reject unknown input keys. It ignores them. So a renamed or
misspelled field fails silently: the run still succeeds, the limit we asked for
is not applied, and the bill arrives at the actor's default. That is exactly how
`maxItems`, `resultLimit` and a missing required `type` survived in this repo
until v1.1.2.

The check does not guess at the payloads. It calls each client method with dummy
arguments and intercepts what would have gone over the wire, so it sees the real
dict, defaults and clamps included.

    python3 scripts/check_actor_inputs.py

Exit codes: 0 clean, 1 a mismatch, 2 the schemas could not be fetched (offline,
or Apify is down) - so a network blip never reads as a passing build.
"""
from __future__ import annotations

import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Apify's CDN answers 403 to urllib's default User-Agent on some edges.
USER_AGENT = "linkedin-skills-actor-check/1 (+https://github.com/sergebulaev/linkedin-skills)"
SCHEMA_URL = "https://api.apify.com/v2/acts/{actor}/builds/default"


def fetch_schema(actor: str) -> dict:
    request = urllib.request.Request(
        SCHEMA_URL.format(actor=actor), headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        build = json.load(response).get("data", {})
    schema = build.get("inputSchema")
    if isinstance(schema, str):
        schema = json.loads(schema)
    if not schema:
        raise RuntimeError(f"{actor}: build has no input schema")
    return schema


def collect_payloads() -> list[tuple[str, str, dict]]:
    """Every (method, actor, payload) the client would send."""
    from lib.apify_client import ApifyClient

    seen: list[tuple[str, str, dict]] = []
    label = {"name": ""}

    def spy(self, actor_id, payload, *, force_refresh=False):
        seen.append((label["name"], actor_id, payload))
        return []

    original = ApifyClient._run_sync
    ApifyClient._run_sync = spy
    try:
        client = ApifyClient.__new__(ApifyClient)          # no token, never runs
        calls = [
            ("fetch_post", lambda: client.fetch_post("https://example.invalid/post")),
            ("fetch_post_comments", lambda: client.fetch_post_comments(post_id="1")),
            ("fetch_user_recent_comments",
             lambda: client.fetch_user_recent_comments(username="someone")),
            ("fetch_post_engagers",
             lambda: client.fetch_post_engagers(post_url="https://example.invalid/post")),
        ]
        for name, call in calls:
            label["name"] = name
            try:
                call()
            except Exception:
                # fetch_post raises when the spy hands back no items. The
                # payload was already recorded, which is all we need.
                pass
    finally:
        ApifyClient._run_sync = original
    return seen


def main() -> int:
    try:
        payloads = collect_payloads()
    except Exception as exc:                                # import or call broke
        print(f"could not collect payloads: {exc}")
        return 1
    if not payloads:
        print("no actor calls intercepted: has the client been restructured?")
        return 1

    schemas: dict[str, dict] = {}
    for _, actor, _ in payloads:
        if actor in schemas:
            continue
        try:
            schemas[actor] = fetch_schema(actor)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print(f"could not fetch the schema for {actor}: {exc}")
            return 2

    problems: list[str] = []
    for method, actor, payload in payloads:
        schema = schemas[actor]
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for key, value in payload.items():
            if key not in properties:
                problems.append(
                    f"{method}: sends {key!r}, which {actor} has no input for. "
                    f"Apify ignores it silently. Known inputs: {sorted(properties)}"
                )
                continue
            maximum = properties[key].get("maximum")
            if maximum is not None and isinstance(value, (int, float)) and value > maximum:
                problems.append(
                    f"{method}: sends {key}={value}, above the actor's maximum of {maximum}"
                )
            enum = properties[key].get("enum")
            if enum and value not in enum:
                problems.append(
                    f"{method}: sends {key}={value!r}, not one of {enum}"
                )

        missing = [
            key for key in required
            if key not in payload and "default" not in properties.get(key, {})
        ]
        if missing:
            problems.append(
                f"{method}: omits {missing}, required by {actor} with no default"
            )
        defaulted = [
            key for key in required
            if key not in payload and "default" in properties.get(key, {})
        ]
        if defaulted:
            problems.append(
                f"{method}: omits required {defaulted}; the actor falls back to "
                f"{ {k: properties[k]['default'] for k in defaulted} }, which is a "
                f"silent behaviour choice rather than ours"
            )

    if problems:
        print("Apify actor input mismatches:\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"OK: {len(payloads)} actor calls across {len(schemas)} actors, "
        "every key is in the actor's schema and every required key is set."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
