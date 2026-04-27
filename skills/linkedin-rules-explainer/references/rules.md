# AI-Tell Rules: Tier-Classified Reference

Fifteen rules from the `linkedin-humanizer` package, sorted by what kind of evidence each one actually represents.

**Tiers:**
- **Forensic** — real AI signal, undefendable. The model or its template leaked.
- **Strict** — real human pattern, but the user banned it for taste. Defending it inside this brand voice is pointless.
- **Aesthetic** — pattern flagged because LLMs use it, not because it signals AI. Famous human writers built careers on these.

**Defense strength:** how well the rule survives a "but a human wrote that" challenge. Low = the rule wins. High = the writer wins.

---

## Tier 1 — Forensic (real AI signals)

### Rule 1. `oaicite` / `contentReference` / `turn0search0` markers

- **Tier:** forensic
- **Why flagged:** These are internal tokens from OpenAI's tool-use scaffold (citation pills, search-result handles). They appear when someone copy-pastes from ChatGPT without cleaning the output. No human types `:contentReference[oaicite:0]{index=0}` by hand.
- **Famous human user:** none. Zero recorded cases.
- **Defense strength:** zero
- **Citation:** Wikipedia, "Signs of AI writing" — https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing

### Rule 2. Knowledge-cutoff disclaimers

- **Tier:** forensic
- **Why flagged:** Phrases like "As of my last update in January 2022…" or "I don't have access to real-time information…" are GPT-3.5/4 training-cutoff boilerplate. A human would write "as of last year" or just give the date.
- **Famous human user:** none.
- **Defense strength:** zero
- **Citation:** Wikipedia "Signs of AI writing"; TechCrunch on OpenAI's discontinued classifier — https://techcrunch.com/2023/07/25/openai-scuttles-ai-written-text-detector-over-low-rate-of-accuracy/

### Rule 3. Phrasal templates left unfilled

- **Tier:** forensic
- **Why flagged:** Visible scaffolding like `[Your Name]`, `2025-XX-XX`, `[Describe section X]`, `[Insert metric here]`. These are prompt-template artifacts where the human forgot to fill the slot.
- **Famous human user:** none.
- **Defense strength:** zero
- **Citation:** Wikipedia "Signs of AI writing"

### Rule 4. Mad-Libs blanks

- **Tier:** forensic
- **Why flagged:** Adjacent to rule 3. Sentences like "I [verb] the [noun] every [time period]" or "The result was a [adjective] [outcome]." These come from instruction-tuned outputs where the model echoed the prompt structure instead of resolving it.
- **Famous human user:** none.
- **Defense strength:** zero
- **Citation:** Wikipedia "Signs of AI writing"

### Rule 5. Em dash overuse — three or more in a single short post

- **Tier:** forensic (at the overuse threshold)
- **Why flagged:** A single em dash is a stylistic choice (see rule 11). But three or more em dashes in a 200-word LinkedIn post is one of the strongest stylometric signals GPT-4 emits. The model uses em dashes to glue clauses where a human would split into two sentences.
- **Famous human user:** Emily Dickinson is the famous defense, but Dickinson used em dashes in poetry across hundreds of poems — not three in a single 200-word business post. Density matters.
- **Defense strength:** low (at the overuse threshold). The single-use defense (rule 11) is high; the overuse case is forensic.
- **Citation:** Wikipedia "Signs of AI writing"; OriginalityAI public stylometry notes

---

## Tier 2 — Strict (corporate-speak, easy ban)

### Rule 6. AI vocabulary: leverage, utilize, harness, delve, foster, cultivate

- **Tier:** strict
- **Why flagged:** Each of these has a one-syllable Anglo-Saxon equivalent (use, use, use, look, build, grow). LLMs over-use the Latinate version because RLHF training samples skewed corporate. Humans use them too — but the user has banned them in his own voice for taste.
- **Famous human user:** any McKinsey deck, any HBR article from 1995–2015. "Leverage" was the management-consulting verb of the 1990s.
- **Defense strength:** medium in the abstract, **zero inside this brand voice** — the user explicitly rejected this register.
- **Citation:** Wikipedia "Signs of AI writing" lists all six under AI vocabulary

### Rule 7. Filler adverbs: fundamentally, essentially, ultimately, crucially

- **Tier:** strict
- **Why flagged:** These are sentence-opener crutches that add no information. "Fundamentally, the issue is X" reduces to "the issue is X." LLMs use them as soft hedges; the user wants them deleted.
- **Famous human user:** academic philosophy papers (Daniel Dennett uses "fundamentally" constantly). Academic register is fine in academia, not in a LinkedIn post.
- **Defense strength:** medium in academic prose, **zero in this voice**.
- **Citation:** Wikipedia "Signs of AI writing"

### Rule 8. Filler openers: "In today's fast-paced world", "In the age of AI"

- **Tier:** strict
- **Why flagged:** These are pure throat-clearing. The post hasn't started yet. LLMs deploy them because the training data is full of corporate blog intros that did the same thing.
- **Famous human user:** every LinkedIn ghost-writer from 2015–2022. The pattern predates GPT.
- **Defense strength:** low. Even before AI, copywriting style guides killed these openers.
- **Citation:** Wikipedia "Signs of AI writing"; Ann Handley, *Everybody Writes* (2014) on opener filler

### Rule 9. Cliché closers: "What do you think?", "Tag someone who needs this"

- **Tier:** strict
- **Why flagged:** Generic engagement bait. LinkedIn's algorithm explicitly penalizes engagement bait under its 2024+ heuristics, and these closers signal the post wasn't written for a specific reader.
- **Famous human user:** every LinkedInfluencer 2016–2022. Pre-dates AI.
- **Defense strength:** low. Even pre-AI, the algorithm hated them.
- **Citation:** LinkedIn engagement-bait policy (in-app community guidelines); Wikipedia "Signs of AI writing"

### Rule 10. Negative parallelism: "X isn't Y, it's Z"

- **Tier:** strict (Sergey's hard ban)
- **Why flagged:** "It's not a bug, it's a feature" / "It's not what you say, it's how you say it." LLMs over-deploy this because RLHF reward models favor it as quotable. The user has explicitly banned it as a personal pattern — too clean, too pat, no friction.
- **Famous human user:** every TED talk 2010–2020. Tony Robbins, Simon Sinek. The pattern is real human rhetoric, but the user rejected it.
- **Defense strength:** medium in oratory, **zero in this voice** (hard ban).
- **Citation:** Wikipedia "Signs of AI writing" under "negative parallelism"

---

## Tier 3 — Aesthetic (overreach, defendable)

### Rule 11. Em dashes — single use

- **Tier:** aesthetic
- **Why flagged:** OriginalityAI and GPTZero both weight em-dash density. The signal collapses below ~3 per 200 words but detectors often flag any em dash as suspicious.
- **Famous human users:**
  - **Emily Dickinson** — built her entire poetic style on em dashes. "Because I could not stop for Death — / He kindly stopped for me —" (1863). Roughly 1,800 poems, em dashes throughout.
  - **Cormac McCarthy** — uses em dashes in *Blood Meridian*, *The Road*, *No Country for Old Men*. McCarthy famously refuses quotation marks; em dashes do dialogue work.
  - **Joan Didion**, *The Year of Magical Thinking* (2005) — em dashes for parenthetical grief.
- **Defense strength:** high (single use). The overuse threshold (3+ in a short post) flips to forensic — see rule 5.
- **Citation:** Stanford HAI / Liang et al. (2023) on detector bias — https://hai.stanford.edu/news/ai-detectors-biased-against-non-native-english-writers ; TechCrunch on OpenAI classifier shutdown for low accuracy — https://techcrunch.com/2023/07/25/openai-scuttles-ai-written-text-detector-over-low-rate-of-accuracy/

### Rule 12. Rule of three

- **Tier:** aesthetic
- **Why flagged:** Triadic structure ("X, Y, and Z") is a top GPT-4 signature. Detectors weight it heavily.
- **Famous human users:**
  - **Lincoln**, Gettysburg Address, 1863: "of the people, by the people, for the people."
  - **Julius Caesar**, 47 BCE: *veni, vidi, vici* — "I came, I saw, I conquered."
  - **Winston Churchill**, House of Commons, 13 May 1940: "blood, toil, tears and sweat" (technically four, but the cadence is built on threes throughout the speech).
  - **Thomas Jefferson**, Declaration of Independence, 1776: "life, liberty, and the pursuit of happiness."
  - **Aristotle**, *Rhetoric*, 4th century BCE — formally identified the rule of three as a foundational rhetorical device.
- **Defense strength:** high. This is 2,400 years of human rhetoric. Flagging it as AI is detector overreach.
- **Citation:** Aristotle, *Rhetoric*, Book III; Stanford HAI on detector false positives

### Rule 13. Passive voice

- **Tier:** aesthetic
- **Why flagged:** GPT-4 over-uses passive constructions. Humanizers strip them by default. But passive voice has legitimate uses — agent-obscuring, formal register, scientific neutrality.
- **Famous human users:**
  - **Watson & Crick**, *Nature*, 25 April 1953: "It has not escaped our notice that the specific pairing we have postulated immediately suggests a possible copying mechanism for the genetic material." Pure passive understatement — the most famous sentence in 20th-century biology.
  - **Joan Didion**, *Slouching Towards Bethlehem* (1968) — uses passive deliberately for narrative distance.
  - **The entire scientific literature** — passive voice is journal house style for a reason. "The samples were treated with…" is correct; "We treated the samples with…" reads as informal.
- **Defense strength:** high in technical/scientific contexts, medium in business writing. Don't strip passive in a research summary.
- **Citation:** Watson & Crick, *Nature* 171:737–738 (1953); Wikipedia "Signs of AI writing" notes passive voice as flagged but contested

### Rule 14. AI vocabulary: "robust"

- **Tier:** aesthetic
- **Why flagged:** Lumped in with leverage/utilize/harness in OriginalityAI's vocabulary list.
- **Famous human users:**
  - **Every epidemiologist for a century** — "robust" has a precise statistical meaning: insensitive to assumption violations. "A robust estimator" is a 1960s term of art (Peter J. Huber, *Robust Statistics*, 1964).
  - **Software engineers** — "robust system" means tolerant of edge cases. Replacing it with "solid" loses meaning.
  - **Immunologists** — "robust immune response" is standard vocabulary in *Nature* and *Cell*.
- **Defense strength:** high in technical writing, medium in business writing. Keep "robust" if it's doing technical work; replace with "solid" only when it's generic praise.
- **Citation:** Peter J. Huber, "Robust Estimation of a Location Parameter," *Annals of Mathematical Statistics* (1964); Stanford HAI on detector bias against technical English

### Rule 15. Curly quotes ("smart quotes")

- **Tier:** aesthetic
- **Why flagged:** Some detectors weight `"` `"` `'` `'` as AI signal because LLM outputs preserve them and human typing usually produces straight `"` and `'`.
- **Famous human users:**
  - **Microsoft Word**, **Google Docs**, **Apple Pages** — all auto-convert straight quotes to curly by default. Anyone typing in those tools produces curly quotes without thinking.
  - **The New Yorker** — house style since 1925 mandates curly quotes. Every published piece uses them.
  - **Every traditionally typeset book since the invention of moveable type** — curly quotes are correct typography. Straight quotes are an ASCII compromise.
- **Defense strength:** high. Flagging curly quotes as AI is detector incompetence — it's flagging Microsoft Word's defaults.
- **Citation:** *The Chicago Manual of Style*, 17th ed., §6.115 on quotation marks; Adelphi University lawsuit illustrating cost of false positives — https://www.plagiarismtoday.com/2025/10/14/adelphi-university-sued-over-ai-allegation/

---

## Summary table

| # | Rule | Tier | Defense | Famous defender |
|---|------|------|---------|------------------|
| 1 | `oaicite` markers | forensic | zero | none |
| 2 | Knowledge-cutoff disclaimers | forensic | zero | none |
| 3 | Phrasal templates `[Your Name]` | forensic | zero | none |
| 4 | Mad-Libs blanks | forensic | zero | none |
| 5 | Em dash overuse (3+ in short post) | forensic | low | none at this density |
| 6 | leverage / utilize / harness / delve / foster / cultivate | strict | medium | McKinsey decks |
| 7 | fundamentally / essentially / ultimately / crucially | strict | medium | Daniel Dennett |
| 8 | "In today's fast-paced world" | strict | low | LinkedIn ghosts 2015–2022 |
| 9 | "What do you think?" / "Tag someone" | strict | low | Influencer playbook |
| 10 | "X isn't Y, it's Z" | strict | medium | TED talks |
| 11 | Em dash (single use) | aesthetic | high | Dickinson, McCarthy, Didion |
| 12 | Rule of three | aesthetic | high | Lincoln, Caesar, Churchill, Aristotle |
| 13 | Passive voice | aesthetic | high | Watson & Crick, Didion, all science |
| 14 | "robust" | aesthetic | high | Huber 1964, all epidemiology |
| 15 | Curly quotes | aesthetic | high | Word/Pages defaults, New Yorker |

---

## Key citations

- **Stanford HAI / Liang et al. (2023)** — AI detectors are biased against non-native English writers. Single most-cited paper for "detectors over-fire on aesthetic patterns." https://hai.stanford.edu/news/ai-detectors-biased-against-non-native-english-writers
- **TechCrunch (25 July 2023)** — OpenAI shut down its own AI-text classifier, citing low rate of accuracy. The company that built GPT couldn't reliably detect GPT. https://techcrunch.com/2023/07/25/openai-scuttles-ai-written-text-detector-over-low-rate-of-accuracy/
- **Wikipedia, "Signs of AI writing"** — community-maintained taxonomy. Source for forensic markers (oaicite, knowledge-cutoff) and the strict vocabulary list. https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- **Adelphi University lawsuit (Oct 2025)** — student sued the university after a false-positive AI accusation. The legal cost of trusting detectors on aesthetic signals. https://www.plagiarismtoday.com/2025/10/14/adelphi-university-sued-over-ai-allegation/

---

**Last Updated:** 2026-04-25
**Maintained By:** Claude Code, for Sergey Bulaev
**Purpose:** Educational backbone for the controversial post arguing that AI-writing rules are forensic in some cases and aesthetic overreach in others.
