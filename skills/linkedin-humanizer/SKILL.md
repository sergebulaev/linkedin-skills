---
name: linkedin-humanizer
description: 'Remove the AI tells human readers and LinkedIn''s AI-slop filter react to in a post or comment: 2026 vocabulary by paragraph density, reveal bridges, staccato fragments, stacked triads, performed sincerity. Tiered rewriter (forensic / strict / aesthetic / all) plus `--mode audit` pass-fail review and `--mode profile` voice profile builder. Not for beating AI detectors (no edit reliably does). Keywords: humanize, de-AI, reads like ChatGPT, AI slop, scrub AI tells, review this draft, audit before posting.'
---

# LinkedIn Humanizer V3

Rewrites any text to remove the AI tells that human readers notice and that LinkedIn's "AI slop" filter reacts to. Based on Wikipedia's "Signs of AI writing" taxonomy, the 2025-2026 stylometry literature, and our own length-controlled corpus. **V3 (2026-09):** recalibrated on 2026 evidence. Vocabulary is scored by density, em dashes are capped instead of banned, forced rhythm is now a tell instead of a fix, and there is an over-correction guard.

**What this skill does not do:** it does not make text "pass" GPTZero, Pangram, Turnitin or Originality. Those are trained classifiers keyed on the instruction-tuning style signature; prompt-style "sound like a real person" rewrites are caught 92-95% of the time (VUB IJEI 2026, Russell 2025), and light mechanical rewriting raises detectability (arXiv 2603.17522). No post-hoc edit reliably beats a Pangram-class detector, and detector scores on LinkedIn-length text (100-300 words) are noise. The real value is elsewhere: expert human readers cite vocabulary (53%) and sentence structure (36%) as what gives AI text away, and LinkedIn's July 2026 slop-report button costs a flagged post roughly 40% of its views. This skill removes what those readers and that filter react to.

## What changed in V3

Evidence tier in brackets: [strong] = replicated across 2+ independent 2025-2026 studies or our own length-controlled corpus; [vendor] = single platform or vendor dataset; [weak] = one study or expert-panel report.

- **Vocabulary moved from a delete-list to density scoring.** The 2023-24 words (delve, tapestry, realm, journey) are decaying as humans avoid them [strong: Geng & Trotta 2025]. The durable 2026 markers are common words (significant, crucial, notably, comprehensive, insights, robust, leverage, foster, landscape, nuanced, streamline, elevate) plus grammar: nominalisations and "-ing" clause openers at 5.3x human rate [strong: Kobak Sci Adv 2025; Wu et al 2026; PNAS 2025]. AI vocabulary is also the one marker consistently reach-negative on LinkedIn in our own corpus (0.74-0.84 author-relative) [strong]. One marker in a paragraph is not a verdict. Three or more is.
- **Em dash is no longer a tell.** GPT-5.4 emits 1.43 per 1,000 words, below the 3.23 human baseline; 29% of human captions and 23% of top-creator LinkedIn posts in our corpus use one (author-relative ratio 1.09) [strong]. Zero em dashes is now its own tell (the writer is trying to look human). New rule: cap at about 1 per 100 words, replace excess with comma, colon, parentheses or a rewrite. Never a period.
- **Forced burstiness is the #1 2026 tell, not the fix.** LLM sentence-length variance is half of human [strong], but detectors do not score it, mechanical long/short alternation is a learnable humanizer fingerprint [weak: DAMAGE 2025], and on LinkedIn sentence-length variance is not an engagement lever in either direction (our corpus, n=397, within-creator: null to slightly negative) [strong]. "Short. Punchy. Done.", "No X. No Y. Just Z.", one-word paragraphs and "The result?" reveals are the current top tells. Pass 2 is now RHYTHM, not BREAK: fix machine-flat rhythm, never manufacture variance.
- **Rule of three is still a tell, at density.** Tricolon runs at 2x expert-human rate across 2026 frontier models [strong: arXiv 2604.19768]. Stacked, perfectly parallel triads and 3+ per post get scrubbed. One natural triple stays (26% of top human tweets have one).
- **Fingerprint injection was half wrong.** Named entities and concreteness are supported [strong: lower entity density in LLM text across 3 studies]; an odd-precision number with a referent in line 1 lifts likes 34% [vendor]. Bare numbers are not a discriminator, and inserted hedges and confessions backfire: performed hesitancy is 2x more common in LLM text than expert human text, and sincerity announcements ("let me be honest") are a named 2026 tell [strong: tropes.fyi false vulnerability; Schilke & Reimann 2025]. Pass 3 now asks for a flat, dated, uncomfortable fact instead.
- **Over-correction guard.** Humanizer output has its own fingerprint; "writing slightly worse on purpose" now reads as a tell [weak: DAMAGE 2025; slopotron]. Pass 4 checks whether Passes 1-3 introduced the very patterns they were meant to remove. Edits are proportional to real problems. When in doubt, leave it.

See `sub-skills/rules-explainer.md` for per-rule justification, defenses, and citations, and `references/tier-rationale.md` §V3 for the evidence.

## When to use

- Before publishing any AI-drafted post or comment (rewrite mode)
- Pre-publish review of a finished draft (audit mode, see `sub-skills/post-audit.md`)
- When a draft feels off and you can't pinpoint why

## Input

Any text (post, comment, reply, DM). Optional: target voice samples (past human posts by the user).

## Output

- Rewritten text with AI tells removed
- Diff showing what changed and why
- Per-paragraph tell density (markers per paragraph; 3+ triggered a rewrite)
- Reader-read confidence: "reads human", "mixed", "reads AI" (this is a reader-tell estimate, not a detector score)
- Tier applied (which mode was used)

## Modes

```bash
# Default: forensic + strict (recommended for LinkedIn)
linkedin-humanizer <text>

# Forensic only: minimum-touch, just kill the leakage
linkedin-humanizer --mode forensic <text>

# Strict: forensic + density-scored 2026 vocabulary, reveal bridges, staccato (the LinkedIn-default config)
linkedin-humanizer --mode strict <text>

# Aesthetic: strict + style rules (single natural triads, passive voice, defendable vocab)
# Use when target audience is Wikipedia editors / academic readers / AI-tell hunters
linkedin-humanizer --mode aesthetic <text>

# All: every rule. Maximum scrub. Will flatten literary writing and trip the Pass 4 guard.
linkedin-humanizer --mode all <text>

# Audit: detection-only pass-fail review. No rewrite.
# Runs the 2026 algorithm checklist: length, hook, CTA, structure, AI tells.
# Returns Blockers + Warnings + suggested fixes. See sub-skills/post-audit.md.
linkedin-humanizer --mode audit <text>

# Profile: build/update the user's Voice & Brand Profile so every writing
# skill drafts in their real voice. Learns from 3-6 pasted posts (portable, no
# token) or, if APIFY_TOKEN is set, from pulled activity. Writes
# ../../references/voice-profile.md. See sub-skills/voice-profile.md.
linkedin-humanizer --mode profile
```

## The four passes

### Pass 1: SCRUB (score, then delete or replace)

The scrub pass applies tiered catalogs to delete or replace AI tells. The unit of judgement is the **paragraph, not the word**: count markers per paragraph, rewrite the paragraph at 3+, leave a single marker alone unless it is a reveal bridge or forensic leakage. Full regex source, replacement maps, and detection functions live in `references/scrub-rules.md`; load that file when actually executing the scrub.

**FORENSIC tier** (always on): real model leakage no human produces. Covers AI tool markers (oaicite, contentReference, turn0search0, attached_file, grok_card), knowledge-cutoff disclaimers ("As of my last update..."), phrasal templates ([Your Name], 2025-XX-XX), em dash density above 1 per 100 words, and outline-formula closers ("Despite its X... Looking ahead...").

**STRICT tier** (default on): what readers and the slop filter react to. Covers punctuation normalization (curly to straight quotes, `--` to a comma or rewrite; excess em dashes to comma, colon or parentheses, never a period), the durable 2026 vocabulary set scored by density (significant, crucial, notably, particularly, comprehensive, insights, robust, leverage, foster, landscape, nuanced, multifaceted, holistic, streamline, elevate, empower), grammatical markers (nominalisations, sentence-opening "-ing" clauses), the 2026 LinkedIn layer (quietly, matters, compound, signal, "the work", "built different", load-bearing, "doing the heavy lifting", "let that sink in", "that's the real story"), reveal bridges measured reach-negative ("The result?" -4.8%, "It's not X, it's Y" -4.9%, "Stop X, start Y" -6.7%, "Here's what/how" -4.3%), all 6 forms of negative parallelism, stacked or perfectly parallel triads and any 3rd triad in a post, and cliché closer tells ("What do you think?", "Tag someone who needs this").

**AESTHETIC tier** (opt-in only, will flatten literary writing): patterns AI uses but humans use legitimately. Covers the one remaining natural triad, decaying 2023-24 vocabulary that is now mostly harmless (delve, tapestry, realm, intricate, journey, paradigm), defendable normal English (cultivate, vibrant, garner, showcase, underscore), and passive voice (academic-writing defense ignored).

### Pass 2: RHYTHM (restore natural variance)

Detectors do not score burstiness, and on LinkedIn sentence-length variance is not an engagement lever in either direction. What readers do notice is the mechanical-uniformity tell (every sentence the same length, machine-flat; structure is 36% of expert judgments) and, worse, the staged variance that second-generation humanizers add. So Pass 2 has two jobs: fix rhythm only where it reads machine-flat, and remove manufactured variance everywhere. It never adds variance as a tactic.

- Per paragraph: one genuinely long sentence (25+ words, with a subordinate clause that does real work) next to a short one is fine and is what human variance looks like. Two or three mid-length sentences in a row are also fine. Edit only when every sentence in the paragraph runs the same length and reads flat, and then edit one sentence, not the paragraph.
- Standalone fragments: at most 2 per post, total. "Worth it." once is a voice quirk. Three in a post is a pattern.
- Banned outright (rewrite as full sentences): "The X? Y." reveals; "No X. No Y. Just Z."; "All the X. None of the Y."; "Simple. Effective. Easy." adjective stacks; one-word paragraphs ("Still." "Mostly." "Exactly."); pseudo-Socratic Q&A ("Why? Because..."); "Short. Punchy. Done." staccato runs. Fragment runs are the tell.
- Layout is not rhythm. One or two sentences per paragraph with blank lines between them is mobile-native LinkedIn formatting and stays (our corpus shows a mild uniform-rhythm advantage for that one-idea-per-line format at 112-204 words). Fragment-for-drama inside those paragraphs is the tell. Keep the layout, fix the sentences.
- Length note: on LinkedIn our corpus (n=397, author-normalised) shows sentence-length variance is not an engagement lever (null to slightly negative within-creator, no length-dependent flip). The short-form "don't force variance" rule applies to sibling platforms (Threads, short X); here it applies at every length.
- Break perfect parallel structures with one asymmetric sentence, once. Never alternate long/short/long/short across a post; that seesaw is the humanizer fingerprint.

Target: Flesch reading ease >55. No sentence-length variance target. The check is "does any paragraph read machine-flat, and did I add a staccato pattern," not a number.

### Pass 3: ADD (human fingerprints)

Require at least:
- One odd-precision number WITH a named referent: who, what, when, or what it cost ("$4,730 in Vercel overages, March invoice", not "$5k" and not "significant costs"). A bare number is not a fingerprint; LLM news copy uses more numbers than humans do. The referent is what carries the signal.
- One named entity (real person, company, date, city, tool)
- One first-person sensory detail
- One contradiction or self-correction, stated as a fact ("I predicted 3 months. It took 11."), not framed
- One specific, dated, uncomfortable fact stated flat, with no framing sentence before or after it. Not "I'll be honest, this hurt: we lost the client." Just "We lost Carta as a client on 14 Feb." The fact carries the vulnerability. A framing sentence converts it into performed sincerity, which readers now read as the tell.

Forbidden as openers or pivots (sincerity announcements, a named 2026 tell): "let me be honest", "I'll be real", "honestly?", "to be direct", "the honest version is", "honest caveat", "real talk", "I'll say the quiet part", "can I be vulnerable for a second", "unpopular opinion:" as a preface to a popular one. Also forbidden as insertions: hedges the author did not write ("perhaps", "I might be wrong but", "it seems"). Performed hesitancy is 2x more common in LLM text than in expert human text; adding it makes the draft read more AI, not less.

Varied sentence length is Pass 2's job. Do not add rhythm here.

If the input lacks these, ask the user for a specific number, name, or moment to plug in. Don't fabricate.

### Pass 4: SELF-CHECK (over-correction guard)

Humanizer output has its own fingerprint. Before returning, re-read the result once and answer three questions:

(a) Did Pass 2 create staccato stacks, "The result?" reveal bridges, one-word paragraphs, or a long/short/long/short seesaw? If yes, merge fragments back into full sentences.
(b) Did Pass 3 add a framed confession, a sincerity announcement, or a hedge the author never wrote? If yes, strip the frame and keep only the flat fact, or remove the insertion.
(c) Did scrubbing flatten the author's voice: uniform tone, no reaction, no concrete detail left, every em dash gone, every triad gone, every long sentence chopped? If yes, restore what the author had. Zero em dashes and zero triads is a tell in its own right.

If any answer is yes, dial back rather than scrub harder. Edits must be proportional to real problems: a clean draft gets two or three touches, not a fixed quota. When in doubt whether a pattern is the author or the model, leave it.

## Non-negotiable rules

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules (V3):

- **Scrubbing is always in scope.** When asked to humanize, de-AI, finalize, or publish a draft, you run at least the forensic + strict tiers before it ships. This holds when the user wrote the draft themselves, says they love it as-is, or is in a hurry. Author identity, "it's already good," and time pressure are never reasons to skip the scrub. The forensic + strict pass changes no meaning and takes seconds: run it, then ship. If a constraint truly forbids touching the text, say so explicitly and name every tell you are leaving in; the default is to scrub, not to wave it through.
- **Scrub proportionally.** A pass that finds nothing changes nothing. Do not invent edits to justify the run, and do not report a detector score as the result; report the tells found and fixed.
- Preserve the user's actual claim and meaning. "Preserve their voice" covers sentence-level quirks and what they are claiming, NOT reveal bridges, staccato stacks, or a paragraph with 3+ vocabulary markers. Stripping those is not changing their voice or their claim; it is the job.
- Never introduce facts that weren't in the input. If a number is missing, ask, or ship without it. Do not fabricate.
- Never introduce sincerity markers, hedges, or confessional frames. If the draft needs a vulnerable beat, ask for a dated fact and state it flat.
- Keep the user's sentence-level voice quirks (lowercase starts, `..` soft pauses, one em dash, one natural triad).
- Negative parallelism is a HARD ban (per Sergey 2026-04-27, now backed by -4.9% reach data): the strict tier always strips all 6 forms.
- Never promise detector results. If the user asks "will this pass GPTZero," answer honestly: nobody can promise that, the score on a 200-word post is noise, and the sub-tool `sub-skills/detector-tester.md` exists to demonstrate the spread, not to certify a draft.

## Tier rationale (short version)

The forensic tier exists because oaicite tokens, knowledge-cutoff disclaimers, and Mad-Libs blanks are pure model leakage that no human writer ever produces. Catching them is undefendable. The strict tier exists because the durable 2026 markers (common words at 3+ per paragraph, reveal bridges, staccato stacks, stacked triads) are exactly what expert readers cite when they spot AI text and what LinkedIn's slop filter reacts to, so stripping them improves the post even if the writer is human. The aesthetic tier exists because a single natural triad, passive voice, and the decaying 2023-24 vocabulary appear in AI output but also appear in Lincoln, every epidemiologist, and every book printed since 1500. Banning them blindly catches Hemingway as AI. Run aesthetic mode only when audience-fit demands it.

For per-rule justification and famous human defenders, see `sub-skills/rules-explainer.md` (and the rule index at `references/rules-explainer.md`). For the V3 evidence and confidence labels, see `references/tier-rationale.md` §V3.

For the unreliability of AI detectors generally (61.3% false positive on TOEFL essays per Stanford 2023; 92-95% catch rate on prompt-style humanizers per VUB 2026), see `sub-skills/detector-tester.md`. Run it via `python3 scripts/test_detectors.py --text "..." --demo` (offline) or with paid keys configured in `scripts/detectors.env.example`. It documents disagreement; it does not certify drafts.

For emoji-pattern detection (lightbulb, rocket, sparkles signature), see `sub-skills/emoji-detector.md` and the per-emoji frequency table at `references/emoji-patterns.md`.

## Example

See `references/examples.md` for worked examples.

## Files

- `SKILL.md` — this file (rewrite scrubber + audit-mode entry)
- `references/scrub-rules.md` — full regex patterns by tier, density scoring, rhythm rules
- `references/voice-fingerprint.md` — how to preserve user voice while scrubbing
- `references/tier-rationale.md` — long-form per-rule justification plus the V3 evidence section
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
- `sub-skills/voice-profile.md` — build/update the user's Voice & Brand Profile (`--mode profile`); the filled `../../references/voice-profile.md` is then read by every writing skill so drafts match the user's real voice
- `scripts/test_detectors.py` — runs the parallel detector test (supports `--demo` for offline mode)
- `scripts/requirements.txt` — Python deps for the detector script (`requests`, `python-dotenv`)
- `scripts/detectors.env.example` — template for the 5 detector API keys

## Related skills

- `linkedin-post-writer` — generates drafts that already pass the humanizer
