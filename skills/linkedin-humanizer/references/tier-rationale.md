# Tier Rationale — Why Three Modes Exist

V1 of this humanizer applied every rule equally. We learned that some rules catch real AI output and some catch good human writing. V2 split them into 3 tiers so users can pick which signals to trust. V3 (2026-09) re-sorted the rules inside those tiers on 2026 evidence: see §V3 recalibration at the end.

## Contents

- The core insight
- Tier 1 - FORENSIC (always on)
- Tier 2 - STRICT (default on)
- Tier 3 - AESTHETIC (opt-in only)
- Recommended default
- What this tiering rejects
- V3 recalibration (2026 evidence, with confidence labels)

## The core insight

AI-detection rules cluster into 3 groups by their relationship to actual AI generation:

1. **Pure leakage** — patterns no human writer ever produces. Catching them is undefendable. (Forensic tier)
2. **Bad-style overlap** — patterns AI uses heavily that are also bad style for humans. Catching them is defendable on style grounds even when origin is unclear. (Strict tier)
3. **Good-writing overlap** — patterns AI uses heavily that are also normal in human writing. Catching them blindly flags Dickinson, Lincoln, and every epidemiologist as AI. (Aesthetic tier)

Most humanizer tools mix all three together as one undifferentiated rulebook. That's why their output flattens literary writing while still missing real AI leakage.

## Tier 1 — FORENSIC (always on)

These are real AI signals. Every detector agrees. No human writer produces them. No defense exists.

### Why they're forensic

- **oaicite / contentReference / turn0search0**: ChatGPT internal tool tokens that leak when the user copy-pastes raw output without cleanup. No human writes these.
- **"As of my last update January 2024"**: model-internal disclaimer about training cutoff. Humans don't disclaim their knowledge cutoff.
- **`[Your Name]` / `2025-XX-XX` / `[Describe X]`**: literal placeholder text from prompt templates that wasn't filled in.
- **Em dash density above ~1 per 100 words**: the *frequency* signal, not the character itself. Emily Dickinson has 1-2 em dashes in a poem; GPT-4 averaged 4-6 in a LinkedIn post. GPT-5.4 is down to 1.43 per 1,000 words, below the human 3.23, so the character alone proves nothing (see §V3). The old glue habit (3+ in a short post) is still leakage-grade.

### Citations

- Wikipedia "Signs of AI writing" forensic-rule section: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Russell, Karpinska, Iyyer (2025) "People who frequently use ChatGPT are accurate detectors" — empirical confirmation that frequent users spot real leakage with high accuracy.

## Tier 2 — STRICT (default on)

Corporate-speak. Bad LinkedIn style regardless of who wrote it. AI uses these because the training corpus did. Banning them improves the post even if the writer is human.

### Why they're strict

- **The durable 2026 vocabulary (significant, crucial, notably, comprehensive, insights, robust, leverage, foster, landscape, nuanced, streamline, elevate, empower)**: common words LLMs over-select at 2-5x human rate across every 2026 frontier model. They are ordinary English, which is exactly why they survive while "delve" dies. Scored by density: one per paragraph is English, three is a signature.
- **Grammar markers (nominalisations, "-ing" clause openers)**: "Leveraging our data, we..." runs at 5.3x the human rate. Readers feel the register shift even when they cannot name it.
- **fundamentally / essentially / ultimately**: filler adverbs that add no information. Strunk & White flagged these in 1918. They were bad style before AI existed.
- **"in today's fast-paced world"** and the reveal bridges ("The result?", "Here's what", "Stop X, start Y"): openers and pivots that LinkedIn measurably down-ranks (-4.3% to -6.7% reach, vendor data). Removing them improves reach regardless of who wrote them.
- **Negative parallelism ("X isn't Y, it's Z")**: per Sergey's 2026-04-27 hard ban, now backed by -4.9% reach data. Used by JFK historically, but in 2026 LinkedIn context it reads as ChatGPT in 90% of cases.
- **Stacked or perfectly parallel triads, and any third triad in a post**: tricolon at 2x expert-human density in 2026 models. The form is innocent; the density and the interchangeable items are the tell. One natural triad stays.
- **Staccato stacks and reveal bridges** ("Short. Punchy. Done.", "No X. No Y. Just Z.", one-word paragraphs): the top 2026 reader-cited tell, and the signature of every prompt-style humanizer. V2 used to add these. V3 removes them.

### The defense (and why we override it)

A reader could argue "leverage" appears in legitimate business writing or "notably" appears in every journal. True, and that is why V3 scores density instead of deleting words: one is left alone. But a paragraph with three of them, on LinkedIn, in 2026, with this audience, signals corporate or AI 90%+ of the time. The cost of rewriting that paragraph is near-zero. The cost of leaving it is a reader assumption that the post is AI-drafted, and possibly a slop report. So strict mode rewrites over-threshold paragraphs by default.

### Citations

- Juzek & Ward (2025) "Why Does ChatGPT 'Delve' So Much?": https://arxiv.org/abs/2412.11385
- Kobak et al. (2025) "Excess vocabulary in LLM-assisted biomedical writing", Science Advances 11/27.
- Wu et al. (2026) cross-model excess-vocabulary replication (GPT-5.5, Claude 4.8, Gemini 3.1).
- PNAS (2025) on present-participial clause openers and nominalisation rate in LLM prose.
- arXiv 2604.19768 (2026) on tricolon density across frontier models.

## Tier 3 — AESTHETIC (opt-in only)

Patterns AI uses but humans use legitimately. Banning them blindly catches Hemingway as AI.

### The 5 most controversial rules in this tier

#### Em dashes (the last one under the cap)
- **Defense**: Emily Dickinson built her poetry on em dashes. Cormac McCarthy uses them throughout *The Road* and *Blood Meridian*. The *New Yorker* has used em dashes as house style since 1925. And in 2026 the frontier models use *fewer* than humans (GPT-5.4: 1.43 per 1,000 words vs. human 3.23). The Economist called it "no longer a reliable sign." 29% of human captions in our own corpus use one.
- **The real signal isn't the character.** It's frequency above ~1 per 100 words (covered in forensic tier). Below that, self-censoring your dashes is itself the tell of someone trying to look human.
- **When to use aesthetic mode**: writing for audiences that still treat any dash as suspicious. Otherwise leave the one dash alone, and never replace it with a period (fragment stacking is the worse tell).

#### Rule of three (the last natural one)
- **Defense**: Lincoln "of the people, by the people, for the people." Caesar veni vidi vici. Churchill "blood, toil, tears and sweat." Aristotle codified the tricolon in 350 BCE. 26% of top human tweets contain exactly one.
- **Banning the tricolon bans 2,400 years of speechwriting.**
- **The real signal**: empty triplets where the three items are interchangeable ("dynamic, vibrant, and innovative"), perfectly parallel triads, and 3+ per post (2x expert-human density in 2026 models). The form is innocent; the density and the hollow content are the tell. Strict mode already scrubs those. Aesthetic mode removes the last natural one.

#### Passive voice
- **Defense**: Watson & Crick (1953): *"It has not escaped our notice..."* Joan Didion *"The center was not holding."* Orwell himself used 20%+ passives in his own essays. Scientific, legal, news writing all require passive.
- **Banning passive flags 60%+ of the *Economist* and *Nature* as AI.**
- **When to use aesthetic mode**: opinion-writing audiences expecting active voice. Never apply to scientific or legal writing.

#### "Cultivate" / "vibrant" / "delve" / "tapestry" / "journey"
- **Defense**: *Cultivate* is George Eliot's signature in Middlemarch. *Vibrant* opens Toni Morrison's Nobel lecture. And the 2023-24 poster words (delve, tapestry, realm, journey) are now decaying: humans avoid them, models are being tuned away from them, and a single "delve" in 2026 is more likely a human joke than a leak (Geng & Trotta 2025).
- **Banning normal English because LLMs use it confuses signal with corpus.** LLMs use these words because they read every English-language book published since 1500.
- **The real signal**: density of the durable common-word set ("robust", "foster", "significant", "notably" at 3+ per paragraph), covered in strict tier. Note that "robust" and "foster" moved from aesthetic to strict in V3 because they survived the 2025-26 vocabulary shift; "robust" as a statistical term of art is still exempt.

#### Curly quotes / typographer's quotes
- **Defense**: Curly quotes happen automatically when typing in Word, Google Docs, Pages, or Notes. Em dashes are produced by autocorrect on every Apple device. Calling these AI tells flags anyone who writes in a real word processor.
- **The real signal**: copy-paste of raw model output where typography wasn't normalized. Strict-mode handles this conversion to straight quotes by default.

### Citations

- Stanford HAI / Liang et al. 2023 "AI detectors biased against non-native English writers": https://hai.stanford.edu/news/ai-detectors-biased-against-non-native-english-writers
- TechCrunch on OpenAI killing its own classifier at 26% accuracy: https://techcrunch.com/2023/07/25/openai-scuttles-ai-written-text-detector-over-low-rate-of-accuracy/
- Newby v. Adelphi University (Oct 2025): https://www.plagiarismtoday.com/2025/10/14/adelphi-university-sued-over-ai-allegation/
- Boston Globe "AI didn't kill the em dash" (May 2025)
- Algorithmic Bridge / Alberto Romero "In Defense of the Em Dash"

## Recommended default

For LinkedIn posts and comments by founders / creators / serious writers in 2026:

```
linkedin-humanizer --mode strict <text>
```

This applies forensic + strict but leaves aesthetic patterns alone. It catches real AI leakage and corporate-speak without flattening the writer's voice. Aesthetic mode is for the rare case where audience-fit demands maximum scrub (e.g., contributing to Wikipedia, posting in an AI-detection-paranoid academic forum).

## What this tiering rejects

The previous one-size-fits-all approach pretended every rule had equal weight. That was wrong. A post with `oaicite[^1]` left in is genuinely AI-leaked. A post using "robust" to describe a statistical model is not. Treating them as equally suspicious creates two problems: false positives on legitimate writing, and false confidence that running through the humanizer means a post is "human." This tiering is the honest version.

## V3 recalibration (2026 evidence, with confidence labels)

Confidence labels: **[strong]** = replicated across 2+ independent 2025-2026 studies or our own length-controlled corpus (X n=445, Threads n=311); **[vendor]** = single platform or vendor dataset; **[weak]** = one study or an expert-panel report.

### 1. Detectors are not the target

GPTZero, Pangram, Turnitin and Originality are trained classifiers keyed on the RLHF instruction-tuning style signature. GPTZero dropped perplexity and burstiness from its score in 2023. Pangram 4 ships a dedicated humanization head. Prompt-style "sound like a real person" rewrites are caught 92-95% of the time (VUB IJEI 2026; Russell 2025) [strong]. Light mechanical rewriting *raises* detectability (arXiv 2603.17522) [weak]. GPTZero states its vocabulary tool is not connected to its score. And LinkedIn-length text (100-300 words) is where every detector is least reliable [strong].

Consequence: the skill no longer promises to pass any detector, and no rule in this file is justified by "detector X weights it." The two targets that remain real are **expert human readers** (who cite vocabulary 53% and sentence structure 36% of the time when they spot AI text) [weak: expert panel] and **LinkedIn's slop filter** (July 2026 report button; flagged posts lose roughly 40% of views) [vendor].

### 2. Vocabulary: density, not deletion

The conspicuous 2023-24 words (delve, tapestry, realm, intricate, journey, paradigm) are decaying as humans avoid them (Geng & Trotta 2025) [strong]. The durable 2026 markers are common words: significant, crucial, notably, particularly, comprehensive, insights, robust, leverage, foster, landscape, nuanced, multifaceted, holistic, streamline, elevate, empower (Kobak Sci Adv 2025; Wu et al 2026 across GPT-5.5 / Claude 4.8 / Gemini 3.1) [strong]. Plus grammar: nominalisations and present-participial "-ing" clause openers at 5.3x human rate (PNAS 2025) [strong]. Plus a LinkedIn-specific 2026 layer (quietly, matters, compound, signal, "the work", "built different", load-bearing, "doing the heavy lifting", "let that sink in", "that's the real story") [vendor]. Reveal bridges are reach-negative on LinkedIn: "The result?" -4.8%, "It's not X, it's Y" -4.9%, "Stop X, start Y" -6.7%, "Here's what/how" -4.3% [vendor].

Our own LinkedIn corpus agrees on the vocabulary side: AI vocabulary is the one marker consistently reach-negative within-creator (0.74-0.84 author-relative) [strong], so the vocabulary pass stays even though its word list changed.

Consequence: the signal is density per paragraph. 3+ markers = rewrite the paragraph. 1 = leave it, unless it is a reveal bridge or negative parallelism (single-hit scrub because of the reach data).

### 3. Em dash: capped, not banned

GPT-5.4 emits 1.43 em dashes per 1,000 words, below the human baseline of 3.23. The Economist (2026): "no longer a reliable sign." Isolated em dashes carry no LinkedIn reach penalty [vendor]. 29% of human Instagram captions use one, and 23% of top-creator LinkedIn posts do, at an author-relative ratio of 1.09 (our 2026-09 LinkedIn corpus, n=397) [strong]. Self-censoring your dashes is itself the tell of someone trying to look human.

Consequence: cap at ~1 per 100 words (1-2 per post). Replace the excess with a comma, colon, parentheses or a rewrite. Never a period, because a split dash creates fragment stacking, which is a worse tell than the dash.

### 4. Rule of three: still a tell, at density

Tricolon runs at 2x expert-human density across 2026 frontier models (arXiv 2604.19768) [strong]. 26% of top human tweets use exactly one [strong: corpus].

Consequence: scrub stacked or perfectly parallel triads and any third triad in a post. Leave one natural one with concrete, non-interchangeable items.

### 5. Burstiness: restore, do not force

LLM sentence-length SD is about half of human [strong], but no detector scores it, and mechanical long/short alternation is itself a learnable humanizer fingerprint (DAMAGE 2025) [weak]. The top 2026 reader-cited tells are exactly forced rhythm: "Short. Punchy. Done.", "No X. No Y. Just Z.", "All the X. None of the Y.", "Simple. Effective. Easy.", "The result?" reveals, one-word paragraphs ("Still." "Mostly."), pseudo-Socratic "Why? Because." [strong: multiple 2026 tell lists + our corpus]. On LinkedIn specifically, sentence-length variance is not an engagement lever in either direction: our author-normalised corpus (keyword n=205 + 15 top creators n=192, 2026-09) shows within-creator CV ratios of 0.96 / 0.80 / 0.92 across length bands, Spearman -0.06, no length-dependent flip, and a mild uniform-rhythm advantage for one-idea-per-line posts at 112-204 words [strong]. The earlier X/Threads result ("bursty wins on long posts") was an author confound and collapses after normalisation; it applies to sibling platforms, not here.

Consequence: Pass 2 is RHYTHM, not BREAK, and rhythm is not a reach tactic. Its only positive goal is to avoid the mechanical-uniformity tell that expert readers notice (structure = 36% of their judgments): do not leave a paragraph machine-flat, but never manufacture variance. One genuinely long sentence next to a short one is fine; fragment runs are the tell. Fragments capped at 2 per post. Staccato patterns banned. Broetry layout (1-2 sentence paragraphs, blank lines) is fine and mobile-native; fragment-for-drama is the tell.

### 6. Fingerprints: concreteness yes, confession no

Concreteness (named entities, dates, what it cost) is a supported human fingerprint: LLM text has lower named-entity density in 3 studies [strong]. An odd-precision number in the first line lifts likes +34% [vendor]. But bare numbers are not a discriminator; LLM news copy uses more numbers than humans [strong]. Inserted hedges and confessions backfire: "performed hesitancy" is 2x more common in LLM text than expert human text; humanizers built on confession cues were caught 100% by expert readers [weak: single study, but the direction is consistent]; sincerity announcements ("let me be honest", "I'll be real", "honestly?") are a named 2026 tell (tropes.fyi "false vulnerability") [vendor]; discovered inauthenticity is the steepest trust loss (Schilke & Reimann 2025) [strong]. A specific, dated, uncomfortable fact stated flat is reach-positive (+4.6% to +10%) [vendor].

Consequence: Pass 3 asks for one odd-precision number WITH a named referent, one named entity, and one flat dated uncomfortable fact with no framing sentence. It never inserts hedges or sincerity markers, and Pass 1 strips them when they open or pivot a draft.

### 7. Over-correction is the new tell

Humanizer output has its own fingerprint (DAMAGE 2025; the slopotron de-slop skill's own findings) [weak]. "Writing slightly worse on purpose" now reads as a tell. Zero em dashes, zero triads, zero long sentences and a flat, reaction-free tone together read as "processed."

Consequence: Pass 4 SELF-CHECK. Edits proportional to real problems, no fixed quota. When in doubt whether a pattern is the author or the model, leave it.
