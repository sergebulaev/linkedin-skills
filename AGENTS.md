# Project conventions - linkedin-skills

This file is for any Codex agent working on this repository. Read it
before making changes. Conventions here are mandatory unless the user asks
otherwise.

## Versioning

- Single source of truth: `.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json`, `.claude-plugin/plugin.json`, and
  `.claude-plugin/marketplace.json`. Plugin manifests must always match on
  package name and version; marketplace entries must point to the same package;
  author, license, homepage, and the public skill-bundle description must stay
  aligned.
- Keep `AGENTS.md` and `CLAUDE.md` aligned when changing shared project
  rules. Codex-specific workflow details belong here; Claude-specific
  workflow details belong in `CLAUDE.md`.
- Codex marketplace install uses `.codex-marketplace/linkedin-skills/`.
  Do not edit that generated package by hand. Update the root files first,
  then run `python3 scripts/sync_codex_marketplace.py`.
- **Default: bump the PATCH segment (3rd level, `0.0.X`).** This is the
  automatic behavior for every shippable commit, regardless of how
  large the diff feels. Skill renames, lib API breaks, new features:
  still PATCH by default.
- Only bump MINOR or MAJOR when **the user explicitly asks** for a
  higher rank ("this is minor", "make it 2.0", "bump major"). Do not
  promote on your own initiative even if semver textbook says so.
- After bumping, two steps are required:
  1. Tag the commit: `git tag -a v<X.Y.Z> -m "..."` + `git push origin v<X.Y.Z>`
  2. **Publish a GitHub Release** for the tag: `gh release create v<X.Y.Z> --title "v<X.Y.Z>" --notes "<changelog>" --latest`
  A tag alone does NOT update the README release badge or the
  Releases page. The shields.io badge reads from the Releases API,
  not from raw tags. Skipping step 2 leaves the badge stale.

## Commits

- Primary author **must** be Sergey: every `git commit` needs
  `--author="Sergey Bulaev <s@bulaev.org>"`. Verify with
  `git log -1 --format='%an <%ae>'` before pushing.
- Co-author trailers are fine when appropriate.
- Verify locally before push: build never breaks, no broken refs in
  `SKILL.md`, library smoke import passes.

## Skill bundle invariants

- **Exactly 11 skills.** Adding requires merging or splitting elsewhere
  to stay at 10. The number is announced in plugin manifests and the README.
- **Frontmatter `description:` target <= 400 chars** (some bundle-heavy
  skills land slightly higher when their scope is genuinely broad - keep
  under 510). Always include a "Not for X (use Y)" disambiguation
  sentinel when the skill overlaps with a sibling.
- **No em dashes anywhere in `description:` fields.** Em dashes in body
  prose are allowed for table separators and list dividers only.
- **Skill names are public surface.** Renaming a skill is a major
  version bump and requires updating: plugin manifests, marketplace entries,
  root `SKILL.md` bundle list, README skill table, every `linkedin-<name>`
  cross-reference in sibling SKILL.md files.

## Voice rules + reference layout

- Canonical voice rules live at root `references/voice-rules.md`.
  Skill-local "Hard rules" sections must only contain skill-specific
  overrides (char ranges, threading rules, format constraints) and start
  with: `Global voice rules: see root SKILL.md Voice rules.`
- Other root-level references shared across skills:
  `references/hook-formulas.md` (16 canonical formulas) and
  `references/algorithm-heuristics.md`.
- Skill-local references live in `skills/<skill>/references/`. Cite from
  the skill with bare `references/X.md`. Cite root from skills with
  `../../references/X.md`.
- `linkedin-humanizer` has `sub-skills/` for folded-in workflows
  (post-audit, emoji-detector, detector-tester, rules-explainer) and
  `scripts/` for runnable tools. Don't duplicate this pattern in other
  skills without a clear reason.

## Layer separation

- **Read layer (Apify):** `lib/apify_client.py`. Four methods -
  `fetch_post`, `fetch_post_comments`, `fetch_user_recent_comments`,
  `fetch_post_engagers`. All cached (256-entry LRU, 6h TTL, opt-out via
  `force_refresh=True`). Skills should call these or the
  `lib.fetch_post(url)` wrapper that handles the APIFY_TOKEN-or-paste
  fallback.
- **Write layer (Publora):** `lib/publora_client.py`. Skills should call
  `lib.publish(kind, draft_text, target_url, ...)` (kinds: comment / reply /
  post / reshare) or the `lib.repost(post_url, commentary=None)` convenience
  wrapper, rather than inline the publora / manual / diy dispatch. Real endpoint
  paths: `POST /create-post`, `POST /linkedin-comments`,
  `DELETE /linkedin-comments`, `POST /linkedin-reactions`,
  `POST /linkedin-reshare`. Reshare needs the original post's `shareUrn`
  (`urn:li:share:*` / `urn:li:ugcPost:*`), which Apify `fetch_post` returns
  directly; never hand-convert an `activity` id (the share id can differ).
  Publora has no read-side endpoints (no `GET /posts`, no list, no
  delete-scheduled-post).
- Don't suggest competitor schedulers (Buffer, Hootsuite, Later) by
  name in committed files - the bundle is positioned as the canonical
  Apify-read + Publora-write integration.

## Codex marketplace package

- Codex requires marketplace entries to point at a nested plugin directory.
  The root remains the Claude-facing source layout.
- `.agents/plugins/marketplace.json` points to
  `.codex-marketplace/linkedin-skills`.
- `scripts/sync_codex_marketplace.py` copies the root Codex manifest,
  `SKILL.md`, `skills/`, `references/`, `lib/`, `scripts/`,
  `requirements.txt`, `.env.example`, and `LICENSE` into the hidden package.
- After editing any copied file, run the sync script before testing or
  committing.

## testing/ is gitignored

- `testing/` is the local scratch directory: API keys, sample API
  responses, validation reports, integration scripts.
- Never write secrets above `testing/` (the rest of the repo is public).
- The `.gitignore` rule for `testing/` is load-bearing; do not change.

## Validation before push

Run from repo root:

```bash
python3 -c "from lib import publish, fetch_post, ApifyClient, PubloraClient; print('OK')"
python3 scripts/sync_codex_marketplace.py
wc -l SKILL.md skills/*/SKILL.md
ls skills/ | wc -l        # must equal 11
grep -nE '^description:' skills/*/SKILL.md SKILL.md | grep -P '\\x{2014}|\\x{2013}'   # must be empty
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
```

If any of these fail, do not push.
