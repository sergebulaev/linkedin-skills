---
name: linkedin-post-writer
description: Draft a new LinkedIn post from scratch using one of 16 2026 hook formulas (anaphora, R.I.P., year-pivot, time-anchor, curiosity-gap, contrarian, emotional cold-open, named-gratitude, and more), picked by engagement goal (comments, reposts, likes, saves). Runs the humanizer pass and schedules via Publora on approval. Use when the user asks to write a post, needs a hook, or wants a proven format. Not for reviewing existing drafts (use linkedin-humanizer --mode audit).
---

# LinkedIn Post Writer

Ship long-form LinkedIn posts using hook formulas that actually performed in 2025-2026 (verified engagement multipliers).

## When to use

- User says "write me a LinkedIn post about X"
- User has a topic + a rough angle and needs a hook + structure
- User wants to pick from known-winning formats and fill in their voice
- User wants to audit + schedule in one flow

## Formulas this skill can use

| Code | Formula | Reference eng | Best for |
|---|---|---|---|
| F1 | Platform Risk Anaphora | 4,240 | Category/platform posts, product-as-fix |
| F2 | R.I.P. Obituary | 3,822 | Era-ending claims, industry pivots |
| F3 | Year-over-Year Pivot | 494, 3.74x | Identity shifts, founder reflection |
| F4 | Time-Anchor Confession | 1,519+ | Vulnerability, voice reset, ICP re-targeting |
| F5 | Self-Proving Meta | 1,082 / 435 comments | Commitment-based posts, tests in public |
| F6 | Comment-Gate Lead Magnet | 717-3,008 | List building (use sparingly, capped reach) |
| F7 | Odd-Precision Money Ledger | 1,755, 9.4x | Founder build-log, cost breakdowns |
| F8 | Paid-vs-Free Reversal | 550, 19.64x | Free framework give-away |
| F9 | Curiosity-Gap Teaser | 306, 4.25x | Emergent behavior, behind-the-scenes |
| F10 | Contrarian + Historical Receipts | 3,083 | Sacred-cow takes, AI/tech cycles |
| F11 | Emotional Cold-Open | high-reach* | Real story with emotional stakes (likes) |
| F12 | Permission Slip | comment-heavy* | Encouragement, reassurance (comments) |
| F13 | Bait-and-Switch Reversal | high-reach* | Policy/process change that's an upgrade (likes) |
| F14 | Named Gratitude / Tribute | repost-heavy* | Thanking mentors / team / departing colleague (reposts) |
| F15 | Explain-to-Kids | save-heavy* | Demystifying jargon (saves) |
| F16 | Status-Strip Humility | like-heavy* | Senior voice wanting warmth not distance (likes) |

\* F11-F16 reach is absolute 2026-corpus reach (often source-driven: a reshare or a famous author), NOT a baseline multiplier like the F1-F10 numbers. The two columns measure different things and are not comparable: F11's "256k" is raw reach, F8's "550, 19.64x" is a format multiplier. Do not rank formulas by putting these side by side. See `../../references/hook-formulas.md` for each formula's real reference and caveats.

Full skeletons in `../../references/hook-formulas.md`. F1-F10 are the long-form thought-leadership set; F11-F16 (validated against a 2026 corpus of above-average performers) skew shorter and emotional and each carries a primary engagement goal.

### Pick by goal first

If the user knows what they want the post to earn, start here, then narrow by topic. Canonical mapping: `../../references/hook-formulas.md` → Engagement-goal split.

| Goal | Reach for |
|---|---|
| Comments | F4, F10, F12, F9 |
| Reposts | F14, F2, F8 |
| Likes | F11, F13, F16 |
| Saves | F15, F7, F8 |

## Steps

1. **Gather inputs.** Topic, angle, draft ideas if the user has them, target audience (founders / operators / marketers), desired length (short 300-500 / medium 900-1300 / long 1500-1900 chars).
2. **Pick the formula.** First ask (or infer) the goal: comments, reposts, likes, or saves. Use the "Pick by goal first" table to shortlist, then suggest 2-3 formulas that also fit the topic and let the user pick. Show the reference engagement number next to each.
3. **Draft the post.** Fill the formula skeleton with user voice. Respect the 2026 algorithm rules:
   - Hook in first 210 chars (before "… see more")
   - 900-1,300 char sweet spot for text posts
   - Double line-breaks between ideas, not single
   - 0-2 hashtags, placed at end
   - No external links in body (move to first comment)
4. **Humanizer pass.** Strip em dashes, AI vocab, rule-of-three, generic openers. Add at least 1 specific number, 1 named entity, 1 first-person concrete detail per 100 words.
5. **Run audit.** Optionally invoke `linkedin-humanizer --mode audit` for algorithm + voice checks before showing to user.
6. **Approval card.** Show: formula used, full draft, char count, suggested posting window (Tue/Wed/Thu 7:30-9:00 AM local), reaction targets from likely commenters.
7. **On approval.** Call `lib.publish(kind="post", draft_text=<approved>, target_url="https://www.linkedin.com/post/new/", platforms=[{"platform":"linkedin","platformId":<id>}], scheduled_time=<iso_or_None>, media_urls=<list_or_None>)`. The wrapper handles Publora / manual / diy routing.

## Hard rules (from user feedback)

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules:

- Never frame LinkedIn as inferior in a LinkedIn post (algo penalty).
- Don't name-drop the user's product in a way that reads as self-promo. One mention max, and only when it's the natural conclusion, not the pitch.
- Include at least one moment of real vulnerability or concrete stakes. Pure insight posts don't land in 2026.
- Vary sentence length aggressively. Mix 3-word sentences and 25-word sentences.

## Anti-patterns (skill will refuse)

- All-caps first line ("THIS CHANGED EVERYTHING."). This holds even for F11 Emotional Cold-Open: carry the intensity with word choice, never caps.
- Em dashes anywhere
- "In today's fast-paced world" openers
- Rule-of-three lists without receipts
- "Game-changer", "deep dive", "leverage", "fundamentally"
- External links in the body
- Reused engagement-bait closers ("tag someone who needs this")

## Resources

- `../../references/hook-formulas.md` — all 16 formula skeletons with worked examples
- `../../references/algorithm-heuristics.md` — 2026 posting rules (timing, format, length)
- `references/humanizer-checklist.md` — the full scrub list

## Related skills

- `linkedin-humanizer` — aggressive AI-tell scrubber, plus `--mode audit` for pre-publish review
- `linkedin-hook-extractor` — reverse-engineer a hook from a viral post you admire
