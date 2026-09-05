# LinkedIn Post Audit

Run any post draft through the 2026 heuristic checklist. Catches AI tells, timing/format issues, length violations, and structural weaknesses before publishing.

## When to use

- Before publishing a hand-written or AI-drafted post
- When `linkedin-post-writer` finishes a draft (auto-invoked)
- When a recent post didn't land and the user wants a post-mortem

## Input

- A post draft (plain text)
- Optional: target audience, scheduled time, format (text / carousel / video / image)

## Output

- **Pass/Fail** header
- **Blockers** (must fix before publishing): em dash density over the cap, paragraphs at 3+ AI markers, reveal bridges, external links in body
- **Warnings** (ship-risky): staccato stacks, sincerity markers, missing referenced numbers, generic close
- **Score estimates:** per-paragraph tell density, approximate first-hour reach fit. No detector score: on 100-300 word text those are noise and the skill does not promise to beat them
- **Suggested fixes:** inline rewrites for each issue
- **Timing recommendation:** best window given audience

## Checks

### Blockers (auto-fail)
1. Em dash density above ~1 per 100 words (1-2 per post); en dash between clauses; double dash. A single em dash is not a blocker
2. External link in body (not in first comment)
3. Post exceeds 3,000 chars (LinkedIn hard limit)
4. Opens with "In today's fast-paced world...", a reveal bridge ("Here's what", "Stop X, start Y"), or a sincerity announcement ("Let me be honest")
5. Ends with "What do you think?", "Thoughts?", "Let that sink in."
6. Any paragraph with 3+ vocabulary / grammar markers, or any negative-parallelism / "The result?" reveal bridge (see `../references/audit-ai-tells.md`)
7. Frames LinkedIn as inferior in a LinkedIn post (algo penalty)

### Warnings (flag with suggested fix)
8. Hook doesn't fit in first 210 chars (mobile `…see more` cutoff)
9. Length outside 900-1,300 sweet spot (or 1,500-1,900 for long-form with breaks)
10. A paragraph that reads machine-flat (4+ sentences all the same length, no clause doing work). Flag that paragraph only; sentence-length variance is not a reach lever on LinkedIn, so never suggest adding variance as a tactic
11. No odd-precision number with a named referent (a bare number does not clear this)
12. No named entity
13. No first-person sensory detail
14. Stacked or perfectly parallel rule-of-three, or 3+ triads in the post (one natural triad passes)
15. More than 2 hashtags
16. User's own product named more than once
17. Missing reaction-prompting moment: a specific, dated, uncomfortable fact stated flat, or an opinion with stakes. A framed confession ("I'll be honest, this hurt") does not clear this; the frame is the tell
18. Passive voice >10%
18a. Staccato stacks ("Short. Punchy. Done.", "No X. No Y. Just Z.", "All the X. None of the Y."), one-word paragraphs, more than 2 standalone fragments, or a long/short/long/short seesaw
18b. Hedging stack or sincerity marker mid-post ("perhaps", "it seems", "honestly?", "real talk")
18c. Over-scrubbed: uniformly flat tone, zero em dashes and zero triads in a long post, no reaction or opinion anywhere
19. First line is not a complete standalone hook (it needs line 2 to make sense). 2026 corpus: every top post front-loads a full hook before the fold.
20. No blank line after the hook / wall-of-text open. Winners use heavy whitespace: one idea per line, blank line after the hook.
21. Emoji sprinkled mid-text in a narrative post, or more than 2-3 total in prose. Top posts front-load 1-2 meaningful emoji; serious/contrarian posts use zero. Exempt: structured glossary/list formats (e.g. F15 Explain-to-Kids) where one emoji anchors each line on purpose.
22. Comment-gate ("comment X and I'll DM you...") in a post whose goal is thought leadership. Organic top performers use zero hard comment-gates; only flag-clear when the post's goal is list-building (then F6 is intentional).
23. No clear primary goal: the post chases comments, reposts, likes, and saves all at once. Pick one (see `../../../references/hook-formulas.md` "Engagement-goal split").

### Info (neutral notes)
24. Suggested posting time given audience
25. Format recommendation (text / carousel / video) given topic
26. Similar-hook detection: if this post's first 100 chars match a recent post

## Steps

1. Parse draft into sentences, paragraphs, first-210-char hook.
2. Run each blocker check; collect failures.
3. If any blockers, return **FAIL** with specific fix suggestions; optionally offer auto-rewrite.
4. If no blockers, run warnings.
5. Report per-paragraph tell density (markers per paragraph, em dashes per 100 words, fragment count, triad count). Do not estimate a detector score.
6. Return structured report.

## Example

See `../references/audit-examples.md` for worked examples.


## Related skills

- `linkedin-humanizer` — aggressive rewrite if audit fails
- `linkedin-post-writer` — regenerate draft using a proven formula
