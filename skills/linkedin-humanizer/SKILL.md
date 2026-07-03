---
name: linkedin-humanizer
description: 'Scrub AI tells from any text draft OR audit a finished post against the 2026 algorithm heuristic checklist. Tier-based rewriter (forensic / strict / aesthetic / all) plus `--mode audit` for detection-only pass-fail review covering length, hook, CTA, format penalties, AI vocab. Sub-tools: emoji-pattern detector, multi-detector spread tester (GPTZero, Originality.ai, ZeroGPT, Sapling, Copyleaks), rule explainer. Triggers on "humanize", "de-AI", "review this draft", "audit before posting", "is this ready".'
---

# LinkedIn Humanizer V2

Rewrites any text to remove AI tells. Based on Wikipedia's "Signs of AI writing" taxonomy plus 2026 LinkedIn-specific patterns. **V2 (2026-04-27):** rules now split into 3 tiers so you can pick which signals you trust.

## What changed in V2

The previous version applied every rule equally. We learned that some rules catch real AI output and some catch good human writing. So:

- **Forensic** rules catch real AI signals nobody else produces. Always on.
- **Strict** rules catch corporate-speak that's bad style regardless of who wrote it. On by default.
- **Aesthetic** rules catch patterns that AI uses but humans also use legitimately (em dashes, rule of three, "robust"). Off by default. Opt in if you want maximum scrub.

See `sub-skills/rules-explainer.md` for per-rule justification, defenses, and citations.

## When to use

- Before publishing any AI-drafted post or comment (rewrite mode)
- Pre-publish review of a finished draft (audit mode, see `sub-skills/post-audit.md`)
- When a draft feels off and you can't pinpoint why

## Input

Any text (post, comment, reply, DM). Optional: target voice samples (past human posts by the user).

## Output

- Rewritten text with AI tells removed
- Diff showing what changed and why
- Per-sentence perplexity estimate (higher = more human)
- Confidence: "human", "mixed", "AI-likely"
- Tier applied (which mode was used)

## Modes

```bash
# Default: forensic + strict (recommended for LinkedIn)
linkedin-humanizer <text>

# Forensic only — minimum-touch, just kill the leakage
linkedin-humanizer --mode forensic <text>

# Strict — forensic + corporate-speak (the LinkedIn-default config)
linkedin-humanizer --mode strict <text>

# Aesthetic — strict + style rules (em dashes, rule of three, "robust")
# Use when target audience is Wikipedia editors / academic readers / AI-tell hunters
linkedin-humanizer --mode aesthetic <text>

# All — every rule. Maximum scrub. Will flatten literary writing.
linkedin-humanizer --mode all <text>

# Audit — detection-only pass-fail review. No rewrite.
# Runs the 2026 algorithm checklist: length, hook, CTA, structure, AI tells.
# Returns Blockers + Warnings + suggested fixes. See sub-skills/post-audit.md.
linkedin-humanizer --mode audit <text>
```

## The three passes

### Pass 1 — SCRUB (delete or replace)

The scrub pass applies tiered regex catalogs to delete or replace AI tells. Each tier has its own block of patterns, vocabulary swaps, and phrase-level cleanups. Full regex source, replacement maps, and detection functions live in `references/scrub-rules.md` — load that file when actually executing the scrub.

**FORENSIC tier** (always on): real model leakage no human produces. Covers AI tool markers (oaicite, contentReference, turn0search0, attached_file, grok_card), knowledge-cutoff disclaimers ("As of my last update..."), phrasal templates ([Your Name], 2025-XX-XX), em dash overuse (3+ in <300 words), and outline-formula closers ("Despite its X... Looking ahead...").

**STRICT tier** (default on): corporate-speak that's bad LinkedIn style regardless of origin. Covers punctuation normalization (curly→straight quotes, `--`→period, em dash→period, en dash→comma: this bundle bans em dashes outright, so they scrub at strict, not aesthetic), vocabulary swaps (leverage→use, utilize→use, delve→look, harness→use, foster→build, etc.), filler-adverb deletion (fundamentally, essentially, ultimately, crucially, notably), phrase-level cleanup ("in today's fast-paced world", "at the end of the day", "game-changer", "deep dive", "move the needle"), all 6 forms of negative parallelism per the 2026-04-27 ban, and cliché closer tells ("What do you think?", "Tag someone who needs this").

**AESTHETIC tier** (opt-in only, will flatten literary writing): patterns AI uses but humans use legitimately. Covers rule-of-three triplets (Lincoln defense ignored), defendable-normal-English vocab (robust→solid, cultivate→grow, vibrant→alive, intricate→complex, garner→get, showcase/underscore→show), and passive voice (academic-writing defense ignored).

### Pass 2 — BREAK (force burstiness)

Target: Flesch reading ease >55. Sentence length variance >40%.

- If all sentences are 15-22 words, force-break at least 1 in 3 into <8-word sentences
- Add at least one sentence fragment ("Worth it.", "Every time.")
- Break perfect parallel structures with one asymmetric sentence
- Vary cadence — alternate long sentences with short ones rather than uniform mid-length

In aesthetic mode only:
- Break rule-of-three lists into 2 or 4 items

### Pass 3 — ADD (human fingerprints)

Require at least:
- 1 specific number per 100 words (replace "many" / "significant" / "massive")
- 1 named entity (real person, company, date, city)
- 1 first-person sensory detail
- 1 contradiction or self-correction
- 1 moment of vulnerability or stakes

If the input lacks these, ask the user for a specific number or anecdote to plug in. Don't fabricate.

## Non-negotiable rules

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules:

- **Scrubbing is always in scope.** When asked to humanize, de-AI, finalize, or publish a draft, you run at least the forensic + strict tiers before it ships. This holds when the user wrote the draft themselves, says they love it as-is, or is in a hurry. Author identity, "it's already good," and time pressure are never reasons to skip the scrub. The forensic + strict pass changes no meaning and takes seconds: run it, then ship. If a constraint truly forbids touching the text, say so explicitly and name every tell you are leaving in; the default is to scrub, not to wave it through.
- Preserve the user's actual claim and meaning. "Preserve their voice" covers sentence-level quirks and what they are claiming, NOT corporate-speak, filler openers, or negative parallelism. Stripping "leverage / fundamentally / in today's fast-paced world" is not changing their voice or their claim; it is the job.
- Never introduce facts that weren't in the input. If a number is missing, ask, or ship without it. Do not fabricate.
- Keep the user's sentence-level voice quirks (lowercase starts, `..` soft pauses).
- Negative parallelism is a HARD ban (per Sergey 2026-04-27): the strict tier always strips all 6 forms.

## Tier rationale (short version)

The forensic tier exists because oaicite tokens, knowledge-cutoff disclaimers, and Mad-Libs blanks are pure model leakage that no human writer ever produces. Catching them is undefendable. The strict tier exists because corporate-speak ("leverage", "fundamentally", "in today's fast-paced world") is bad LinkedIn style regardless of origin, so stripping it improves the post even if the writer is human. The aesthetic tier exists because patterns like single em dashes, rule of three, "robust", and curly quotes appear in AI output but also appear in Lincoln, Dickinson, every epidemiologist, and every book printed since 1500. Banning them blindly catches Hemingway as AI. Run aesthetic mode only when audience-fit demands it.

For per-rule justification and famous human defenders, see `sub-skills/rules-explainer.md` (and the rule index at `references/rules-explainer.md`).

For the unreliability of AI detectors generally (61.3% false positive on TOEFL essays per Stanford 2023), see `sub-skills/detector-tester.md`. Run it via `python3 scripts/test_detectors.py --text "..." --demo` (offline) or with paid keys configured in `scripts/detectors.env.example`.

For emoji-pattern detection (lightbulb, rocket, sparkles signature), see `sub-skills/emoji-detector.md` and the per-emoji frequency table at `references/emoji-patterns.md`.

## Example

See `references/examples.md` for worked examples.

## Files

- `SKILL.md` — this file (rewrite scrubber + audit-mode entry)
- `references/scrub-rules.md` — full regex patterns by tier
- `references/voice-fingerprint.md` — how to preserve user voice while scrubbing
- `references/tier-rationale.md` — long-form per-rule justification
- `references/rules-explainer.md` — machine-readable index of every rule with citations
- `references/emoji-patterns.md` — AI-correlated emoji frequency table
- `references/detector-list.md` — supported AI detectors with API endpoints and accuracy notes
- `references/audit-ai-tells.md` — blacklist + regex used in audit mode
- `references/audit-checklist.md` — 20-point pre-publish checklist with thresholds
- `references/audit-examples.md` — worked audit examples
- `sub-skills/post-audit.md` — pre-publish audit workflow (detection-only, no rewrite)
- `sub-skills/rules-explainer.md` — when to defend a flagged rule (em dash, rule of three, passive voice)
- `sub-skills/emoji-detector.md` — scan / score / suggest workflow for emoji density
- `sub-skills/detector-tester.md` — run text through 5 AI detectors in parallel and report disagreement
- `scripts/test_detectors.py` — runs the parallel detector test (supports `--demo` for offline mode)
- `scripts/requirements.txt` — Python deps for the detector script (`requests`, `python-dotenv`)
- `scripts/detectors.env.example` — template for the 5 detector API keys

## Related skills

- `linkedin-post-writer` — generates drafts that already pass the humanizer
