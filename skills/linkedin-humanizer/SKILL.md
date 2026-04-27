---
name: linkedin-humanizer
description: Remove AI tells from any LinkedIn post or comment draft. Tier-based scrubber (forensic / strict / aesthetic / all) that strips real AI signals like oaicite tokens and knowledge-cutoff disclaimers, optionally also corporate-speak (leverage, delve, utilize) and aesthetic patterns (em dashes, rule of three) on demand. Use before publishing any AI-drafted content. Keywords humanizer, AI detection, OriginalityAI, GPTZero, scrub AI tells, rewrite human, forensic, strict, aesthetic.
---

# LinkedIn Humanizer V2

Rewrites any text to remove AI tells. Based on Wikipedia's "Signs of AI writing" taxonomy plus 2026 LinkedIn-specific patterns. **V2 (2026-04-27):** rules now split into 3 tiers so you can pick which signals you trust.

## What changed in V2

The previous version applied every rule equally. We learned that some rules catch real AI output and some catch good human writing. So:

- **Forensic** rules catch real AI signals nobody else produces. Always on.
- **Strict** rules catch corporate-speak that's bad style regardless of who wrote it. On by default.
- **Aesthetic** rules catch patterns that AI uses but humans also use legitimately (em dashes, rule of three, "robust"). Off by default. Opt in if you want maximum scrub.

See `linkedin-rules-explainer` for per-rule justification, defenses, and citations.

## When to use

- Before publishing any AI-drafted post or comment
- When `linkedin-post-audit` flags AI tells
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
```

## The three passes

### Pass 1 — SCRUB (delete or replace)

**FORENSIC tier (always on, real AI leakage):**

```
- oaicite, contentReference, turn0search0, attached_file, grok_card markers → delete entirely
- "As of my last update [DATE]" / "As of my knowledge cutoff" → delete sentence
- Phrasal templates: [Your Name], 2025-XX-XX, [Describe X here] → flag for user fill
- Mad-Libs blanks (consecutive square brackets) → flag for user fill
- Em dash overuse: 3+ em dashes in a post under 300 words → strip to commas/periods
- Outline-formula closer: "Despite its X, faces Y. Looking ahead..." → flag/rewrite
```

**STRICT tier (on by default, corporate-speak):**

Punctuation:
```
- " " → "  (curly quotes to straight)
- ' ' → '  (curly apostrophes to straight)
- -- → . (double dash to period)
```

Vocabulary (regex strip and replace):
```
- leverage → use
- utilize → use
- facilitate → help
- streamline → simplify
- delve → look
- navigate → handle
- unlock → find
- harness → use
- fundamentally → (delete)
- essentially → (delete)
- ultimately → (delete)
- crucially → (delete)
- notably → (delete)
- landscape → field (or delete)
- ecosystem → (contextual)
- paradigm → approach
- realm → area
- seamless → smooth
- holistic → full
- nuanced → specific
```

Phrase-level (full negative parallelism coverage as of 2026-04-27 ban):
```
- "It's not just X, it's Y"        → rewrite as paired declaratives
- "X isn't Y, it's Z"              → rewrite as paired declaratives
- "Not X, but Y"                   → rewrite without inversion
- "It's not about X, it's about Y" → rewrite as direct claim
- "The question isn't X, it's Y"   → rewrite as direct claim
- "This isn't X. This is Y"        → rewrite as direct claim
- "In today's fast-paced world"    → delete opener entirely
- "in the age of AI"               → delete
- "at the end of the day"          → delete
- "game-changer"                   → specific descriptor
- "deep dive"                      → "look" or "analysis"
- "needle-moving"                  → "real"
- "move the needle"                → "change the numbers"
- "paradigm shift"                 → "real shift"
- "What do you think?" closer      → delete or replace with specific question
- "Tag someone who needs this"     → delete
```

**AESTHETIC tier (opt-in only, will flatten literary writing):**

```
- Single em dash use → period or comma (Dickinson defense ignored)
- Rule of three: triplet adjectives or triplet clauses → break to 2 or 4 (Lincoln defense ignored)
- "robust" → solid (every epidemiologist defense ignored)
- "foster" → build (cultural-criticism defense ignored)
- "cultivate" → grow (academic-prose defense ignored)
- "vibrant" → specific descriptor (Toni Morrison defense ignored)
- "intricate" / "intricacies" → "complex"
- "garner" → "get"
- "showcase" → "show"
- "underscore" → "show"
- Passive voice → active where possible (academic writing defense ignored)
```

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

- Preserve the user's actual claim. Humanizing does not mean changing meaning.
- Capitalize all names (Dharmesh, Felix, HubSpot, Claude).
- Never introduce facts that weren't in the input. If a number is missing, ask.
- Keep the user's sentence-level voice quirks (lowercase starts, `..` soft pauses).
- Negative parallelism is a HARD ban (per Sergey 2026-04-27): the strict tier always strips all 6 forms.

## Tier rationale (short version)

The forensic tier exists because oaicite tokens, knowledge-cutoff disclaimers, and Mad-Libs blanks are pure model leakage that no human writer ever produces. Catching them is undefendable. The strict tier exists because corporate-speak ("leverage", "fundamentally", "in today's fast-paced world") is bad LinkedIn style regardless of origin, so stripping it improves the post even if the writer is human. The aesthetic tier exists because patterns like single em dashes, rule of three, "robust", and curly quotes appear in AI output but also appear in Lincoln, Dickinson, every epidemiologist, and every book printed since 1500. Banning them blindly catches Hemingway as AI. Run aesthetic mode only when audience-fit demands it.

For per-rule justification and famous human defenders, see the `linkedin-rules-explainer` skill.

For the unreliability of AI detectors generally (61.3% false positive on TOEFL essays per Stanford 2023), see the `linkedin-detector-tester` skill.

For emoji-pattern detection (lightbulb, rocket, sparkles signature), see the `linkedin-emoji-detector` skill.

## Example

> **Input:**
> "In today's fast-paced landscape, businesses must fundamentally leverage AI to unlock robust ROI. It's not just about adoption, it's about transformation. As of my last update in January 2024, the trends are clear — here's what I've learned."
>
> **Output (default mode = forensic + strict):**
> "businesses need AI to cut costs. adoption is the easy part. transformation is the actual work. here's what we learned running 35k LinkedIn profiles through our system daily."
>
> **Diff:**
> - FORENSIC: removed "As of my last update in January 2024" disclaimer
> - FORENSIC: removed em dash overuse
> - STRICT: removed "in today's fast-paced landscape" opener
> - STRICT: removed "fundamentally", "leverage", "unlock"
> - STRICT: removed "It's not just X, it's Y" negative parallelism, replaced with paired declaratives
> - PASS 3: added specific number (35k) and named entity (LinkedIn)
> - AESTHETIC was NOT applied — "robust" stays if it was actually there in source

## Files

- `SKILL.md` — this file
- `references/scrub-rules.md` — full regex patterns by tier
- `references/voice-fingerprint.md` — how to preserve user voice while scrubbing
- `references/tier-rationale.md` — long-form per-rule justification

## Related skills

- `linkedin-rules-explainer` — per-rule deep dive with citations and defenses
- `linkedin-detector-tester` — run text through 5 AI detectors in parallel, show divergence
- `linkedin-emoji-detector` — flag AI-pattern emoji usage (lightbulb / rocket / sparkles)
- `linkedin-post-audit` — detection-only pass (no rewrite)
- `linkedin-post-writer` — generates drafts that already pass the humanizer

## Changelog

- **2026-04-27 V2** — split rules into forensic / strict / aesthetic tiers. Added `--mode` flag. Added forensic-tier patterns from Wikipedia (oaicite tokens, knowledge-cutoff disclaimers, phrasal templates). Expanded negative parallelism coverage to all 6 forms per Sergey's 2026-04-27 ban.
- **2026-04-08 V1** — initial release.
