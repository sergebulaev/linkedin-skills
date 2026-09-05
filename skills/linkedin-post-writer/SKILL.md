---
name: linkedin-post-writer
description: Draft a new LinkedIn post from scratch using one of 20 2026 hook formulas (anaphora, R.I.P., time-anchor, curiosity-gap, contrarian, controlled A/B, false-binary, and more) plus a founders-edition angle library, picked by engagement goal (comments, reposts, likes, saves). Runs the humanizer pass and schedules via Publora on approval. Use to write a post, find a hook or proven format, or get founder-specific angles. Not for reviewing existing drafts (use linkedin-humanizer --mode audit).
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
| F4 | Time-Anchor Confession | 1,519+ | Vulnerability, voice reset, ICP re-targeting (2026: use with care, see caveats) |
| F5 | Self-Proving Meta | 1,082 / 435 comments | Commitment-based posts, tests in public |
| F6 | Comment-Gate Lead Magnet | 717-3,008 | List building (2026: use with care, real deliverable only, see caveats) |
| F7 | Odd-Precision Money Ledger | 1,755, 9.4x | Founder build-log, cost breakdowns (2026: strongest opener, number-first) |
| F8 | Paid-vs-Free Reversal | 550, 19.64x | Free framework give-away |
| F9 | Curiosity-Gap Teaser | 306, 4.25x | Emergent behavior, behind-the-scenes (2026: use with care, pay off in 2 lines) |
| F10 | Contrarian + Historical Receipts | 3,083 | Sacred-cow takes, AI/tech cycles |
| F11 | Emotional Cold-Open | high-reach* | Real story with emotional stakes (likes) |
| F12 | Permission Slip | comment-heavy* | Encouragement, reassurance (comments; 2026: use with care, needs a dated fact) |
| F13 | Bait-and-Switch Reversal | high-reach* | Policy/process change that's an upgrade (likes) |
| F14 | Named Gratitude / Tribute | repost-heavy* | Thanking mentors / team / departing colleague (reposts) |
| F15 | Explain-to-Kids | save-heavy* | Demystifying jargon (saves) |
| F16 | Status-Strip Humility | like-heavy* | Senior voice wanting warmth not distance (likes) |
| F17 | Controlled A/B Anecdote | structural† | One-variable comparison, delegation/AI takes (comments) |
| F18 | False-Binary Dissolve | structural† | "Both obvious answers fail" governance/strategy (comments/reposts; 2026: it is the post's one contrast) |
| F19 | Anecdote-Meets-Evidence Bridge | structural† | Personal noticing + a data stack (comments/saves) |
| F20 | Diverging-Curves Close | structural† | Two trajectories that diverge, quotable maxim (reposts) |

\* F11-F16 reach is absolute 2026-corpus reach (often source-driven: a reshare or a famous author), NOT a baseline multiplier like the F1-F10 numbers. The two columns measure different things and are not comparable: F11's "256k" is raw reach, F8's "550, 19.64x" is a format multiplier. Do not rank formulas by putting these side by side. See `../../references/hook-formulas.md` for each formula's real reference and caveats.

† F17-F20 are **structural formulas**: they shape the logic of a post (a controlled comparison, a false binary, an evidence bridge, two diverging curves) rather than its topic. They carry no reference number and are chosen by primary goal. They were built for the founders edition and several founder angles pin them by name.

Full skeletons in `../../references/hook-formulas.md`. F1-F10 are the long-form thought-leadership set; F11-F16 (validated against a 2026 corpus of above-average performers) skew shorter and emotional and each carries a primary engagement goal.

### 2026 reach caveats (Sep 2026 audit)

The reference numbers above are unchanged; what changed is how the 2026 feed treats the *device* each formula leans on. Every formula in `../../references/hook-formulas.md` now carries a "2026 reach note"; the ones that matter when picking:

- **Never open with a question.** Question as the first line is -34% median likes across all follower bands (MagicPost, 1.2M posts; vendor data, proprietary AI-score). Move the question to the close, where it is +3%.
- **Prefer number-first.** An odd-precision number in line 1 is +34% median likes (same source). F7 is the strongest 2026 opener; F3, F5, F17 are number-first by construction.
- **F4 Confession, use with care:** a specific, dated, uncomfortable fact with no "let me be honest" / "confession:" framing; substance inside the first 3 lines. Manufactured candor is the "false vulnerability" tell; genuine vulnerability is +7 to +10% (vendor data).
- **F6 Comment-Gate, use with care:** comment-gate CTAs are the named target of LinkedIn's March 2026 authenticity update, and the July 2026 "AI slop" report button cuts flagged posts ~40% views. Only with a real, named deliverable, and never "comment X to get Y" phrasing.
- **F9 Curiosity-Gap, use with care:** teaser phrases ("what nobody tells you", "what most people miss", "the real question is") are on the 2026 AI-tell consensus lists. The gap must be specific and pay off within 2 lines, before the fold.
- **F12 Permission Slip and F18 False-Binary, use with care:** both are generic-frame devices ("Stop X, start Y" -6.7%, "It's not X, it's Y" -4.9%, vendor data). They survive with a dated fact and as the post's only contrast.
- **Density rule:** one contrast and one triple per post, zero "The result?" / "Plot twist:" / "Here's what" bridges. 98-100% of top human creators still use these devices; the tell is repetition plus emptiness, not the device.
- **Still lifts reach:** number-first line, closing question, P.S. sign-off (+7.5%), 1,000+ chars (1.18x) and 20+ sentences (1.14x, AuthoredUp 3M posts), 1-2 sentence paragraphs with blank lines (recommended layout, not a tell).

### Pick by goal first

If the user knows what they want the post to earn, start here, then narrow by topic. Canonical mapping: `../../references/hook-formulas.md` → Engagement-goal split.

| Goal | Reach for |
|---|---|
| Comments | F17, F10, F4, F12, F9 (F4/F12/F9 with their 2026 caveats) |
| Reposts | F14, F2, F8 |
| Likes | F11, F13, F16 |
| Saves | F15, F7, F8 |

## Steps

**Voice profile first (all drafts).** If `../../references/voice-profile.md` has `filled: yes`, load it and match the user's voice fingerprint, hard rules, and CTA/link style throughout. If it is not filled, mention once that `linkedin-humanizer --mode profile` can learn their voice from a few posts, then proceed with the generic voice rules.

**Founder mode (when the writer is a founder).** Before picking a formula, open `../../references/founder-topics.md` and offer a founder **angle** (A1-A10) that fits their goal. The angle picks the *territory* (reprice the category, the scarce-shots math, the delegation line, and so on); several angles pin the formula for you (A9 uses F17, A10 uses F18+F20). Founder angles compound trust with a narrow audience of investors, hires, and design partners rather than chasing broad reach. Fill the angle's bracketed slots with the founder's real numbers, then continue from step 3.

1. **Gather inputs.** Topic, angle, draft ideas if the user has them, target audience (founders / operators / marketers), desired length (short 300-500 / medium 900-1300 / long 1500-1900 chars).
2. **Pick the formula.** First ask (or infer) the goal: comments, reposts, likes, or saves. Use the "Pick by goal first" table to shortlist, then suggest 2-3 formulas that also fit the topic and let the user pick. Show the reference engagement number next to each, plus the formula's 2026 caveat if it has one. Two hook rules apply regardless of formula: **never open with a question** (-34% median likes; the question goes at the close, +3%) and **prefer a number-first line** (+34% median likes; both MagicPost vendor data, proprietary AI-score). If the best hook you have is a question, invert it into the number that answers it.
3. **Draft the post.** Fill the formula skeleton with user voice. Respect the 2026 algorithm rules:
   - Hook in first 210 chars (before "… see more"); line 1 is a statement or a number, never a question, never "Here's what/how", never "Stop X, start Y"
   - 900-1,300 char sweet spot for text posts; 1,000+ chars and 20+ sentences carry a 1.18x / 1.14x reach lift (AuthoredUp 3M posts), so do not trim a substantive post below 1,000 to hit the sweet spot
   - Double line-breaks between ideas, not single; 1-2 sentence paragraphs are the recommended layout
   - One contrast and one triple per post maximum; no "The result?" / "Plot twist:" reveal bridges (Density rule in `../../references/hook-formulas.md`)
   - Close with a specific question, and add a one-line P.S. when there is a real follow-up (+7.5%)
   - 0-2 hashtags, placed at end
   - No external links in body (move to first comment)
4. **Humanizer pass.** Scrub 2026 AI vocab by density, cap em dashes (about one per 100 words), break stacked triads, generic openers and reveal bridges. Add at least 1 specific number, 1 named entity, 1 first-person concrete detail per 100 words.
5. **Run audit.** Optionally invoke `linkedin-humanizer --mode audit` for algorithm + voice checks before showing to user.
6. **Optional illustration.** If the post would land better with a visual (or the user asks), offer one: draft an image and generate it with `lib.illustrate(prompt, kind="wide")`, pulling brand handle/color from Voice & Brand Profile §6 for the overlay. Show the returned `url` + `cost` in the approval card and attach it via `media_urls` on publish. For a **multi-image grid** (2-10 images in one post) use `lib.illustrate_set([p1, p2, ...], kind="wide", overlay=brand)` and pass every `url` in `media_urls=[...]`. Full workflow: `../linkedin-humanizer/sub-skills/illustration.md`. No Pixfaro key -> it drafts the prompt for the user to generate manually.
7. **Approval card.** Show: formula used, full draft, char count, suggested posting window (Tue/Wed/Thu 7:30-9:00 AM local), reaction targets from likely commenters, and the illustration (if any).
8. **On approval.** Call `lib.publish(kind="post", draft_text=<approved>, target_url="https://www.linkedin.com/post/new/", platforms=[{"platform":"linkedin","platformId":<id>}], scheduled_time=<iso_or_None>, media_urls=<list_or_None>)`. The wrapper handles Publora / manual / diy routing.

## Hard rules (from user feedback)

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules:

- Never frame LinkedIn as inferior in a LinkedIn post (algo penalty).
- Don't name-drop the user's product in a way that reads as self-promo. One mention max, and only when it's the natural conclusion, not the pitch.
- Include at least one moment of real vulnerability or concrete stakes. Pure insight posts don't land in 2026.
- Natural rhythm, not manufactured variance: one genuinely long sentence next to a short one per paragraph is fine; never alternate long/short across the post and never stack fragments (at most 2 standalone fragments per post). Touch a paragraph only if every sentence reads the same flat length.

## Anti-patterns (skill will refuse)

- All-caps first line ("THIS CHANGED EVERYTHING."). This holds even for F11 Emotional Cold-Open: carry the intensity with word choice, never caps.
- Question as the first line ("Ever wondered why...?"). Invert to a number, move the question to the close.
- "Here's what / here's how" or "Stop X, start Y" as the opener; "The result?" / "Plot twist:" as a reveal bridge
- Announced candor ("Let me be honest", "Confession:") with no dated fact behind it
- "Comment X to get Y" comment-gate phrasing
- Em dashes above the cap (more than about one per 100 words)
- "In today's fast-paced world" openers
- Rule-of-three lists without receipts
- "Game-changer", "deep dive", "leverage", "fundamentally"
- External links in the body
- Reused engagement-bait closers ("tag someone who needs this")

## Resources

- `../../references/hook-formulas.md` — all 20 formula skeletons with worked examples, per-formula 2026 reach notes, "What still lifts reach in 2026" and the Density rule
- `../../references/founder-topics.md` — founders-edition library of 10 founder angles (A1-A10) with fill-in templates
- `../../references/algorithm-heuristics.md` — 2026 posting rules (timing, format, length)
- `references/humanizer-checklist.md` — the full scrub list

## Related skills

- `linkedin-humanizer` — aggressive AI-tell scrubber, plus `--mode audit` for pre-publish review
- `linkedin-hook-extractor` — reverse-engineer a hook from a viral post you admire
