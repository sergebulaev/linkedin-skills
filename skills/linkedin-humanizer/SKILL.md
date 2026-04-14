---
name: linkedin-humanizer
description: Remove AI tells from any LinkedIn post or comment draft. Aggressive scrubber that strips em dashes, AI vocabulary (leverage, fundamentally, delve, harness), rule-of-three lists, filler openers, and uniform sentence rhythm. Adds human fingerprints (specific numbers, named entities, varied sentence length). Use before publishing any AI-drafted content. Keywords: humanizer, AI detection, OriginalityAI, GPTZero, scrub AI tells, rewrite human.
---

# LinkedIn Humanizer

Aggressively rewrites any text to pass AI detectors and read authentically human. Based on Wikipedia's "Signs of AI writing" taxonomy plus 2026 LinkedIn-specific patterns.

## When to use

- Before publishing any AI-drafted post or comment
- When `linkedin-post-audit` flags AI tells
- When a draft feels "off" and you can't pinpoint why

## Input

Any text (post, comment, reply, DM). Optional: target voice samples (past human posts by the user).

## Output

- Rewritten text with AI tells removed
- Diff showing what changed and why
- Per-sentence perplexity estimate (higher = more human)
- Confidence: "human", "mixed", "AI-likely"

## The three passes

### Pass 1 — SCRUB (delete or replace)

**Punctuation:**
- `—` → `.` or `,`
- `–` → `-` or `to`
- `--` → `.` or `,`
- `" "` → `"`

**Vocabulary (regex-strip and replace):**
- leverage → use
- utilize → use
- facilitate → help
- streamline → simplify
- delve → look
- navigate → handle
- unlock → find
- harness → use
- foster → build
- cultivate → grow
- fundamentally → (delete)
- essentially → (delete)
- ultimately → (delete)
- crucially → (delete)
- notably → (delete)
- landscape → field (or delete)
- ecosystem → (contextual)
- paradigm → approach
- realm → area
- robust → solid
- seamless → smooth

**Phrase-level:**
- "It's not just X, it's Y" → rewrite as a single claim
- "In today's fast-paced world" → delete opener entirely
- "game-changer" → specific descriptor
- "deep dive" → "look" or "analysis"
- "at the end of the day" → delete

### Pass 2 — BREAK (force burstiness)

Target: Flesch reading ease >55. Sentence length variance >40%.

- If all sentences are 15-22 words, force-break at least 1 in 3 into <8-word sentences
- Add at least one sentence fragment ("Worth it.", "Every time.")
- Break rule-of-three lists into twos or fours
- Break perfect parallel structures with one asymmetric sentence

### Pass 3 — ADD (human fingerprints)

Require at least:
- 1 specific number per 100 words (replace "many" / "significant" / "massive")
- 1 named entity (real person, company, date, city)
- 1 first-person sensory detail
- 1 contradiction or self-correction
- 1 moment of vulnerability or stakes

If the input lacks these, ask the user for a specific number or anecdote to plug in. Don't fabricate.

## Non-negotiable rules

- Preserve the user's actual claim. Humanizing ≠ changing meaning.
- Capitalize all names (Dharmesh, Felix, HubSpot, Claude).
- Never introduce facts that weren't in the input. If a number is missing, ask.
- Keep the user's sentence-level voice quirks (lowercase starts, `..` soft pauses).

## Example

> **Input:**
> "In today's fast-paced landscape, businesses must fundamentally leverage AI to unlock robust ROI — here's what I've learned."
>
> **Output:**
> "businesses need AI to cut costs. here's what we learned running 35k LinkedIn profiles through our system daily."
>
> **Diff:** removed em dash, removed "in today's fast-paced landscape", removed "fundamentally", removed "leverage", removed "unlock", removed "robust", added specific number (35k), added named entity (LinkedIn).

## Files

- `SKILL.md` — this file
- `references/scrub-rules.md` — full regex patterns and replacement mapping
- `references/voice-fingerprint.md` — how to preserve user voice while scrubbing

## Related skills

- `linkedin-post-audit` — detection-only pass (no rewrite)
- `linkedin-post-writer` — generates drafts that already pass the humanizer
