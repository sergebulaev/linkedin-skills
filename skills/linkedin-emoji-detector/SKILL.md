---
name: linkedin-emoji-detector
description: Detect AI-pattern emoji usage in any LinkedIn post or comment draft. Counts emoji frequency, compares against the AI-correlated emoji frequency table (lightbulb, rocket, sparkles, recycling, target, chart, key, dart, muscle, fire), and returns an AI-emoji density score (0-100) plus suggested human-pattern alternatives. Three modes: scan, score, suggest. Use before publishing or as a pre-pass to linkedin-humanizer. Keywords: emoji detector, AI emoji, lightbulb tell, rocket tell, sparkles tell, ChatGPT signature, OriginalityAI, GPTZero, MagicPost.
---

# LinkedIn Emoji Detector

Flags AI-pattern emoji usage in LinkedIn drafts before they ship. Built on Naïlé Titah / MagicPost frequency data (Feb 2026) showing lightbulb, rocket, sparkles, and recycling emojis appear 2-3x more often in AI-generated LinkedIn posts than in human-authored ones.

Pattern data from Naïlé Titah / MagicPost LinkedIn analysis (Feb 2026, 220 engagement viral post).

## When to use

- Before publishing any AI-drafted post or comment
- As a pre-pass before `linkedin-humanizer` (catches a tell humanizer doesn't fix)
- When `linkedin-post-audit` flags "feels AI" without a specific reason
- When auditing a backlog of scheduled posts for AI signature emojis

## Input

Any LinkedIn text (post, comment, reply, DM). Optional: mode flag (`--strict`, `--lenient`, `--score`).

## Output

- AI-emoji density score (0-100, higher = more AI-like)
- List of flagged emojis with frequency vs. AI baseline
- Suggested human-pattern alternatives (or removal recommendation)
- Verdict: "clean", "borderline", "AI-likely"

## The three modes

### Mode 1 — SCAN (default)

Walks the text, extracts every emoji, looks up each one in the frequency table at `references/emoji-patterns.md`, and returns a per-emoji report.

For each detected AI-pattern emoji:
- Show the emoji
- Show its AI-correlation frequency (e.g. lightbulb = 2.57%)
- Show count in the draft
- Suggest a human-pattern alternative or recommend deletion

### Mode 2 — SCORE (`--score`)

Returns a single number (0-100). No rewrite, no suggestions.

Formula:
- Each AI-pattern emoji contributes `frequency_pct * count * 10`
- Cap at 100
- Bonus +20 if 3+ distinct AI-pattern emojis present (cluster signal)
- Bonus +15 if a single emoji appears 2+ times (repetition tell)

Verdicts:
- 0-20: clean
- 21-50: borderline
- 51-100: AI-likely

### Mode 3 — SUGGEST

Returns a rewritten emoji set. Keeps the post's emoji count roughly the same but swaps AI-pattern emojis for less-correlated alternatives, or recommends removal where no clean substitute exists.

## Strict vs. lenient

### `--strict`

Flag any AI-pattern emoji at all. One lightbulb = AI-likely verdict. Use when content goes out under a personal brand that has never used emoji-heavy AI patterns.

### `--lenient`

Flag only if 3+ AI-pattern emojis appear in the same post, OR if a single AI-pattern emoji repeats 2+ times. Use for accounts where occasional emoji is fine and only the cluster pattern matters.

Default mode is between the two: flag if score >20.

## Non-negotiable rules

- Never auto-rewrite without showing the diff first
- Preserve emoji count parity if user wants emojis (don't strip and leave nothing)
- Capitalize all names in suggested replacements (Felix, HubSpot, Claude)
- If the post has zero emojis, skip the skill entirely and return "n/a"
- Don't fabricate "human" emoji frequencies — the human-pattern alternatives in `references/emoji-patterns.md` are emojis with sub-1% AI correlation, not emojis proven "more human"

## Example

> **Input:**
> "Excited to share our new feature 🚀 Game-changing AI ✨ Unlock your potential 💡 Let's go 🔥"
>
> **Output (default mode):**
> Score: 78 / 100 — AI-likely
>
> Flagged:
> - 🚀 rocket (3.28% AI freq, 1 use) → consider 📦 or remove
> - ✨ sparkles (3.11% AI freq, 1 use) → remove, no clean swap
> - 💡 lightbulb (2.57% AI freq, 1 use) → 🪛 or remove
> - 🔥 fire (1.31% AI freq, 1 use) → keep or swap to 🌶️
>
> Cluster bonus: +20 (4 distinct AI-pattern emojis)
>
> **Suggested rewrite:**
> "Excited to share our new feature. AI that actually works. Try it. 🌶️"

## Files

- `SKILL.md` — this file
- `references/emoji-patterns.md` — full frequency table + human-pattern alternatives

## Related skills

- `linkedin-humanizer` — runs after emoji detector to scrub AI vocabulary and rhythm
- `linkedin-post-audit` — broader pre-publish check (calls this skill internally)
- `linkedin-post-writer` — generates drafts that already avoid AI-pattern emojis
