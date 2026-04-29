---
name: linkedin-post-writer
description: Draft a viral-ready LinkedIn post using a 2026 hook formula. Use when the user wants to write a new LinkedIn post, needs help with a hook, or wants to pick a proven format (platform-risk anaphora, R.I.P. obituary, year-over-year pivot, time-anchor confession, self-proving meta, paid-vs-free reversal, curiosity-gap teaser, odd-precision money ledger, contrarian historical receipts). The skill drafts the post, runs the humanizer pass, shows an approval card, and schedules via Publora on confirmation. Keywords: linkedin post, viral hook, personal brand, founder post, content draft, thought leadership, 2026 algorithm.
---

# LinkedIn Post Writer

Ship long-form LinkedIn posts using hook formulas that actually performed in 2025-2026 (verified engagement multipliers from Jake Ward, Lara Acosta, Cam Trew, Noam Nisand, Alex Vacca, Richard Illingworth, Naïlé Titah).

## When to use

- User says "write me a LinkedIn post about X"
- User has a topic + a rough angle and needs a hook + structure
- User wants to pick from known-winning formats and fill in their voice
- User wants to audit + schedule in one flow

## Formulas this skill can use

| Code | Formula | Reference eng | Best for |
|---|---|---|---|
| F1 | Platform Risk Anaphora (Jake Ward) | 4,240 | Category/platform posts, product-as-fix |
| F2 | R.I.P. Obituary (Alex Vacca) | 3,822 | Era-ending claims, industry pivots |
| F3 | Year-over-Year Pivot (Cam Trew) | 494, 3.74x | Identity shifts, founder reflection |
| F4 | Time-Anchor Confession (Lara Acosta) | 1,519+ | Vulnerability, voice reset, ICP re-targeting |
| F5 | Self-Proving Meta (Noam Nisand) | 1,082 / 435 comments | Commitment-based posts, tests in public |
| F6 | Comment-Gate Lead Magnet (Illingworth) | 717-3,008 | List building (use sparingly, capped reach) |
| F7 | Odd-Precision Money Ledger (Jake Ward) | 1,755, 9.4x | Founder build-log, cost breakdowns |
| F8 | Paid-vs-Free Reversal (Illingworth) | 550, 19.64x | Free framework give-away |
| F9 | Curiosity-Gap Teaser (Naïlé Titah) | 306, 4.25x | Emergent behavior, behind-the-scenes |
| F10 | Contrarian + Historical Receipts (Jake Ward) | 3,083 | Sacred-cow takes, AI/tech cycles |

Full skeletons in `references/hook-formulas.md`.

## Steps

1. **Gather inputs.** Topic, angle, draft ideas if the user has them, target audience (founders / operators / marketers), desired length (short 300-500 / medium 900-1300 / long 1500-1900 chars).
2. **Pick the formula.** If the user didn't specify, suggest 2-3 formulas that fit the topic and let them pick. Show the reference engagement number next to each.
3. **Draft the post.** Fill the formula skeleton with user voice. Respect the 2026 algorithm rules:
   - Hook in first 210 chars (before "… see more")
   - 900-1,300 char sweet spot for text posts
   - Double line-breaks between ideas, not single
   - 0-2 hashtags, placed at end
   - No external links in body (move to first comment)
4. **Humanizer pass.** Strip em dashes, AI vocab, rule-of-three, generic openers. Add at least 1 specific number, 1 named entity, 1 first-person concrete detail per 100 words.
5. **Run audit.** Optionally invoke `linkedin-post-audit` for algorithm + voice checks before showing to user.
6. **Approval card.** Show: formula used, full draft, char count, suggested posting window (Tue/Wed/Thu 7:30-9:00 AM local), reaction targets from likely commenters.
7. **On approval — adapt to the active backend.** Call `lib.active_backend()`:
   - **`publora`** (PUBLORA_API_KEY set) → schedule via `lib.PubloraClient.create_post` with LinkedIn platformId. If `scheduledTime` omitted, Publora posts ~90s in the future.
   - **`manual`** (no backend configured — the default) → output the approved post via `lib.manual_mode_message(draft_text, target_url="https://www.linkedin.com/post/new/", kind="post")`. User pastes directly into LinkedIn's post composer. Do NOT attempt to publish programmatically.
   - **`diy`** (LINKEDIN_SKILLS_CUSTOM_POSTER set) → invoke the custom poster with the post content + optional media URLs.

## Hard rules (from user feedback)

- No em dashes. Ever. Period.
- Capitalize all names, companies, products.
- Never frame LinkedIn as inferior in a LinkedIn post (algo penalty).
- Don't name-drop the user's product in a way that reads as self-promo. One mention max, and only when it's the natural conclusion, not the pitch.
- Include at least one moment of real vulnerability or concrete stakes — pure insight posts don't land in 2026.
- Vary sentence length aggressively. Mix 3-word sentences and 25-word sentences.

## Anti-patterns (skill will refuse)

- All-caps first line ("THIS CHANGED EVERYTHING.")
- Em dashes anywhere
- "In today's fast-paced world" openers
- Rule-of-three lists without receipts
- "Game-changer", "deep dive", "leverage", "fundamentally"
- External links in the body
- Reused engagement-bait closers ("tag someone who needs this")

## Resources

- `references/hook-formulas.md` — all 10 formula skeletons with worked examples
- `references/algorithm-heuristics.md` — 2026 posting rules (timing, format, length)
- `references/humanizer-checklist.md` — the full scrub list

## Related skills

- `linkedin-post-audit` — run this on any draft before publishing
- `linkedin-humanizer` — aggressive AI-tell scrubber
- `linkedin-hook-extractor` — reverse-engineer a hook from a viral post you admire
