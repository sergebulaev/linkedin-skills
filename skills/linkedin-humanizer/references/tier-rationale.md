# Tier Rationale — Why Three Modes Exist

V1 of this humanizer applied every rule equally. We learned that some rules catch real AI output and some catch good human writing. V2 splits them into 3 tiers so users can pick which signals to trust.

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
- **3+ em dashes in <300 word post**: the *frequency* signal, not the character itself. Emily Dickinson has 1-2 em dashes in a poem; ChatGPT averages 4-6 in a LinkedIn post.

### Citations

- Wikipedia "Signs of AI writing" forensic-rule section: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Russell, Karpinska, Iyyer (2025) "People who frequently use ChatGPT are accurate detectors" — empirical confirmation that frequent users spot real leakage with high accuracy.

## Tier 2 — STRICT (default on)

Corporate-speak. Bad LinkedIn style regardless of who wrote it. AI uses these because the training corpus did. Banning them improves the post even if the writer is human.

### Why they're strict

- **leverage / utilize / harness**: synonyms for "use" that signal corporate context. Humans say "use." McKinsey decks say "leverage." When the audience is LinkedIn founders, "use" wins regardless of provenance.
- **fundamentally / essentially / ultimately**: filler adverbs that add no information. Strunk & White flagged these in 1918. They were bad style before AI existed.
- **"in today's fast-paced world"**: opener cliché that LinkedIn algorithm down-ranks. Removing it improves reach.
- **Negative parallelism ("X isn't Y, it's Z")**: per Sergey's 2026-04-27 hard ban. The pattern is the #1 AI-tell after em dashes. Used by JFK historically, but in 2026 LinkedIn context it reads as ChatGPT in 90% of cases.

### The defense (and why we override it)

A reader could argue "leverage" appears in legitimate business writing or "fundamentally" appears in philosophy. True. But on LinkedIn, in 2026, with this audience, those words signal corporate or AI 90%+ of the time. The cost of stripping them is near-zero. The cost of leaving them in is reader assumption that the post is AI-drafted. So strict mode strips them by default.

### Citations

- Juzek & Ward (2025) "Why Does ChatGPT 'Delve' So Much?": https://arxiv.org/abs/2412.11385
- Kobak et al. (2025) "Excess vocabulary in LLM-assisted biomedical writing", Science Advances 11/27.

## Tier 3 — AESTHETIC (opt-in only)

Patterns AI uses but humans use legitimately. Banning them blindly catches Hemingway as AI.

### The 5 most controversial rules in this tier

#### Em dashes (single use)
- **Defense**: Emily Dickinson built her poetry on em dashes. Cormac McCarthy uses them throughout *The Road* and *Blood Meridian*. The *New Yorker* has used em dashes as house style since 1925.
- **The real signal isn't the character.** It's frequency (covered in forensic tier as 3+ in short post).
- **When to use aesthetic mode**: writing for academic readers / Wikipedia editors / AI-detection-paranoid audiences. Otherwise leave em dashes alone.

#### Rule of three
- **Defense**: Lincoln "of the people, by the people, for the people." Caesar veni vidi vici. Churchill "blood, toil, tears and sweat." Aristotle codified the tricolon in 350 BCE.
- **Banning the tricolon bans 2,400 years of speechwriting.**
- **The real signal**: empty triplets where the three items are interchangeable ("dynamic, vibrant, and innovative"). The form is innocent; the content is what's hollow. Strict-mode burstiness rules already break empty triplets.

#### Passive voice
- **Defense**: Watson & Crick (1953): *"It has not escaped our notice..."* Joan Didion *"The center was not holding."* Orwell himself used 20%+ passives in his own essays. Scientific, legal, news writing all require passive.
- **Banning passive flags 60%+ of the *Economist* and *Nature* as AI.**
- **When to use aesthetic mode**: opinion-writing audiences expecting active voice. Never apply to scientific or legal writing.

#### "Robust" / "foster" / "cultivate" / "vibrant"
- **Defense**: *Robust* is a standard adjective in epidemiology and engineering. *Cultivate* is George Eliot's signature in Middlemarch. *Vibrant* opens Toni Morrison's Nobel lecture. *Foster* is the verb every cultural critic reaches for.
- **Banning normal English because LLMs use it confuses signal with corpus.** LLMs use these words because they read every English-language book published since 1500.
- **The real signal**: corporate-speak words like "leverage" and "fundamentally" (covered in strict tier).

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
