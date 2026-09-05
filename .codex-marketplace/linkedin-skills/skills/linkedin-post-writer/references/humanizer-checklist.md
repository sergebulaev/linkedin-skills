# Humanizer Pre-Publish Checklist (V3, 2026-09)

Every post must pass this before the approval card is shown. If any fail, rewrite that section and re-run. Full rules: `../../linkedin-humanizer/references/scrub-rules.md`. The unit is the paragraph: one marker is English, three is a signature.

## SCRUB (score, then delete or replace)

### Punctuation
- [ ] Em dashes (`—`) at or under ~1 per 100 words (1-2 per post). Replace only the excess, with `,` or `:` or `( )` or a rewrite. Never with `.` (a split dash stacks fragments, a worse tell). Do not push to zero: zero is below the human baseline
- [ ] No en dashes (`–`) between clauses (number ranges stay)
- [ ] No double dashes (`--`)
- [ ] No curly quotes (convert to straight `"`)
- [ ] No Oxford commas in casual posts (too tidy)

### Vocabulary (density per paragraph: 3+ = rewrite the paragraph, 2 = replace the weakest, 1 = leave)
Durable 2026 markers (common words, the ones that survived):
- [ ] significant, crucial, notably, particularly, comprehensive, insights
- [ ] robust, leverage, foster, landscape, nuanced, multifaceted, holistic
- [ ] streamline, elevate, empower
- [ ] fundamentally, essentially, ultimately, crucially
Older corporate verbs (weaker, still counted): utilize, facilitate, harness, unlock, navigate, seamless, ecosystem
Grammar markers (each counts as one):
- [ ] Sentence opening with an "-ing" clause ("Leveraging our data, we...") -> put the actor first
- [ ] Nominalisation ("the implementation of") -> use the verb
2026 LinkedIn layer (each counts as one):
- [ ] quietly, "X matters.", compound, "a signal", "the work", "built different", load-bearing, "doing the heavy lifting", "let that sink in", "that's the real story"
Decaying 2023-24 set (delve, tapestry, realm, journey, paradigm, cultivate): count as one, do not chase alone

### Phrases (single hit = fix; these are reach-negative on LinkedIn)
- [ ] "It's not just X, it's Y" and every negative-parallelism form (-4.9%)
- [ ] "The result?" / "The catch?" reveal (-4.8%)
- [ ] "Stop X, start Y" (-6.7%)
- [ ] "Here's what / how / the thing" (-4.3%)
- [ ] "In today's fast-paced world"
- [ ] "Game-changer"
- [ ] "Deep dive"
- [ ] "At the end of the day"
- [ ] "Needle-moving"

### Structure
- [ ] No paragraph reads machine-flat (every sentence the same length, no clause doing work). Fix that one paragraph only; never manufacture variance. On LinkedIn sentence-length variance is not a reach lever (our corpus: null to slightly negative within-creator)
- [ ] One genuinely long sentence next to a short one is fine; a fragment run is the tell. One-idea-per-line posts keep their uniform rhythm
- [ ] No staccato stacks ("Short. Punchy. Done.", "Simple. Effective. Easy.", "No X. No Y. Just Z.", "All the X. None of the Y.")
- [ ] No one-word paragraphs ("Still." "Mostly.")
- [ ] At most 2 standalone fragments in the whole post
- [ ] No pseudo-Socratic "Why? Because..."
- [ ] Layout is fine: 1-2 sentence paragraphs with blank lines stay. Fragment-for-drama inside them is the tell
- [ ] No perfect parallel structure across a list
- [ ] No hedging stack ("perhaps", "might", "could potentially", "it seems")
- [ ] No sincerity announcement as opener or pivot ("let me be honest", "I'll be real", "honestly?", "to be direct", "the honest version is", "honest caveat")
- [ ] No passive voice >10% of clauses
- [ ] At most one natural rule-of-three; no stacked or perfectly parallel triads, never 3+ in a post
- [ ] No opening with a rhetorical question (on LinkedIn it reads AI)
- [ ] No closing with "What do you think?"

## ADD (human fingerprints)

- [ ] One odd-precision number WITH a named referent: who, what, when, or what it cost ("$4,730 in Vercel overages, March invoice"). Bare numbers do not count; LLM copy uses more numbers than humans
- [ ] ≥1 named entity (real person, company, date, city, tool)
- [ ] ≥1 first-person sensory detail (what you saw, heard, touched)
- [ ] ≥1 contradiction or self-correction stated as fact ("I predicted 3 months. It took 11.")
- [ ] One opinion with stakes: something someone could disagree with
- [ ] One specific, dated, uncomfortable fact stated flat, with no framing sentence before or after it ("We lost Carta as a client on 14 Feb." Not "I'll be honest, this hurt: ..."). The fact carries the vulnerability; the frame turns it into performed sincerity
- [ ] Nothing was inserted that the author did not say: no added hedges, no added confessions, no invented numbers

## SELF-CHECK (over-correction guard)

- [ ] The scrub did not create staccato stacks, reveal bridges, or one-word paragraphs
- [ ] The scrub did not add a framed confession or a hedge
- [ ] The author's tone, reactions, one em dash and one natural triad survived. Uniformly flat prose is a humanizer fingerprint
- [ ] Edits were proportional to real problems. A clean draft gets 2-3 touches, not a quota. When in doubt, leave it

## Target scores

- Flesch reading ease: >55 (conversational)
- Passive voice: <8%
- Vocabulary / grammar markers: no paragraph at 3+
- Em dash density: about 1 per 100 words
- Standalone fragments: at most 2 per post
- Detector scores (GPTZero, Originality, Pangram) are not a target. No post-hoc edit reliably beats them, and on 100-300 word text their output is noise. Do not report one as a result

## DO rules (from 2026 dos-and-donts playbook)

- [ ] Lead with strongest insight first (inverted pyramid) — hook captures in 3 lines
- [ ] Keep length 300-400 words, 20+ sentences (dwell-time optimal)
- [ ] Use line breaks, **bold**, lists for scannability and dwell time
- [ ] End with a **genuine question**, not engagement bait
- [ ] Include at least one real failure or behind-the-scenes moment (failures draw **8.5x more engagement** than polished posts)
- [ ] Make content save-worthy: framework, template, or specific data
- [ ] Post 2-3x per week max, same days/times (audience training)
- [ ] Engage 15-30 min **before AND after** posting (up to +20% reach)
- [ ] Reply to every comment within the first hour (first 90 min = distribution fate)
- [ ] Engage on 10-15 others' posts daily with substantive comments
- [ ] Write from personal experience (validates expertise over marketing)

## Final voice check

- Capitalize all proper names (people, companies, products)
- Capitalize company/product names (HubSpot, Claude, Co.Actor)
- Don't frame LinkedIn as inferior on LinkedIn
- Don't name-drop own product more than once
- One sharp insight, not three vague ones
