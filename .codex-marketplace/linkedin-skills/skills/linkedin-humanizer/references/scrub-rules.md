# Scrub Rules — V3 Tiered (Regex + Replacements + Density)

V3 (2026-09): rules recalibrated on 2026 evidence. Vocabulary is scored by **density per paragraph**, not deleted per word. Em dashes are **capped**, not banned. Forced rhythm is a tell, not a fix. See SKILL.md for tier philosophy and `tier-rationale.md` §V3 for the evidence.

## Contents

- Density scoring (how every vocabulary rule is applied)
- TIER: FORENSIC (always on)
- TIER: STRICT (default on)
- TIER: AESTHETIC (opt-in only)
- Pass 2 - Rhythm restoration (all tiers)
- Pass 3 - Forbidden insertions (sincerity markers, hedges)
- Cliché opener / closer detection (strict tier)
- Preserve these (user voice, don't scrub)
- Comment-reply scrub (when replying to commenters on your own post)
- Announcement-opener scrub (strict tier)

---

## Density scoring (how every vocabulary rule is applied)

The cluster principle: expert readers spot AI text from clusters of markers, not from any single word. One "notably" in a paragraph is English. "Notably", "comprehensive" and a nominalisation in the same paragraph is a signature.

```python
def score_paragraph(paragraph: str, markers: dict) -> dict:
    """Count marker hits per paragraph across all STRICT vocabulary, grammar,
    and LinkedIn-layer lists. Returns hits and the action to take."""
    hits = []
    for name, pattern in markers.items():
        for m in re.finditer(pattern, paragraph, flags=re.I):
            hits.append((name, m.group(0)))
    n = len(hits)
    always = [h for h in hits if h[0] in ("reveal_bridge", "neg_parallel", "sincerity_marker")]
    if n >= 3:
        action = "REWRITE_PARAGRAPH"     # 3+ markers = signal. Rewrite the whole paragraph, not word-by-word.
    elif always:
        action = "REPLACE"               # a reveal bridge / negative parallelism / sincerity marker is always scrubbed,
                                         # even when paired with one ordinary marker (checked BEFORE the density branch)
    elif n == 2:
        action = "REPLACE_WEAKEST"       # 2 ordinary markers = borderline. Replace the one doing least work, leave the other.
    else:
        action = "LEAVE"                 # a single common word is not a verdict
    return {"hits": hits, "count": n, "action": action}
```

Rules of application:
- Score forensic markers separately: one hit = delete, no density threshold.
- Post-level counts also matter for two patterns: triads (3+ per post = scrub down to one) and standalone fragments (3+ per post = merge back, see Pass 2).
- Never replace a word with a synonym from the same list. "Leverage" to "harness" is not a fix.
- When you rewrite a paragraph, rewrite it in the author's register (check `voice-fingerprint.md`), not in "plain" register. Plainness at uniform temperature is itself a fingerprint.

---

## TIER: FORENSIC (always on)

Real model leakage. No human writer ever produces these. Every detector agrees. No defense exists.

### AI tool markers (delete entirely + flag)

```python
FORENSIC_MARKERS = [
    r"\boaicite\b",                          # ChatGPT internal citation token
    r"\bcontentReference\b",                 # ChatGPT artifact
    r"\bturn\d+search\d+\b",                 # OpenAI tool call leakage (turn0search0 etc)
    r"\battached_file\b",                    # Claude/GPT file ref
    r"\bgrok_card\b",                        # Grok artifact
    r"\boai_citation\b",                     # OpenAI citation marker
    r"\bcontentReference\[\^\d+\]",          # numbered citation refs
]
```

### Knowledge-cutoff disclaimers (delete sentence)

```python
CUTOFF_DISCLAIMERS = [
    r"As of my (last update|knowledge cutoff|training cutoff)[^.]*\.",
    r"As of (January|June|October|November) 202\d[^.]*\.",
    r"Based on (information|data) (available|up to) [^.]*\.",
    r"My (knowledge|training data) (cuts off|extends to) [^.]*\.",
    r"I cannot provide (real-time|current|up-to-date) [^.]*\.",
]
```

### Phrasal templates (flag for user fill, do NOT auto-fill)

```python
PHRASAL_TEMPLATES = [
    r"\[Your Name\]",
    r"\[Your Company\]",
    r"\[Describe [^]]+\]",
    r"\[Insert [^]]+\]",
    r"202\d-XX-XX",                          # date placeholder
    r"\[NAME\]|\[DATE\]|\[TOPIC\]",
    r"Mad[\- ]Libs",                         # any literal mention
]
```

### Em dash DENSITY (cap: about 1 per 100 words)

The character is not a tell. GPT-5.4 emits 1.43 em dashes per 1,000 words, below the human baseline of 3.23; 29% of human Instagram captions and 23% of top-creator LinkedIn posts in our corpus use one (author-relative ratio 1.09, i.e. not a reliable tell on LinkedIn). Zero em dashes in a post that wanted one is the tell of someone trying to look human. What is still forensic is the old GPT-4 glue habit: 3+ in a short post.

```python
def em_dash_excess(text: str) -> int:
    """Return how many em dashes exceed the cap (~1 per 100 words, floor 1, ceiling 2 per post).
    0 = leave every em dash alone."""
    words = len(text.split())
    em = text.count("—")
    cap = max(1, min(2, round(words / 100)))
    return max(0, em - cap)

# Replacement order for the EXCESS ones (keep the one doing the most work, usually the first):
#   1. comma            if the dash joins a clause to the main sentence
#   2. colon            if the dash introduces a reveal, a list, or a consequence
#   3. parentheses      if the dash pair wraps an aside
#   4. rewrite          if none of the above reads naturally
# NEVER a period. "X. Y." from a split dash creates fragment stacking, which is a worse tell than the dash.
```

### Outline-formula closers (flag)

```python
OUTLINE_CLOSERS = [
    r"Despite (its|the) [^,]+, faces (challenges|obstacles)[^.]*\.",
    r"Looking ahead, [^.]+ (will|must|should)[^.]*\.",
    r"In conclusion, [^.]+\.",
    r"To summarize,[^.]+\.",
    r"In summary,[^.]+\.",
]
```

---

## TIER: STRICT (default on)

What expert human readers cite when they spot AI text (vocabulary 53%, sentence structure 36%) and what LinkedIn's slop filter reacts to. All vocabulary and grammar lists below go through `score_paragraph()`; reveal bridges and negative parallelism are scrubbed on a single hit.

### Punctuation

```python
STRICT_PUNCT = [
    (r"“|”", '"'),                # curly quotes → straight
    (r"‘|’", "'"),                # curly apostrophes → straight (preserve apostrophe-in-contractions: don't / it's / you're)
    (r"\s*--\s*", ", "),          # double dash → comma (or rewrite). Not a period: a period here stacks fragments.
    (r"\s*–\s*", ", "),           # en dash between clauses → comma (number ranges stay literal e.g. 7-9)
]
# Em dashes are NOT in this list. They are handled by em_dash_excess() above: only the excess over
# ~1 per 100 words is replaced, and the replacement is comma / colon / parentheses / rewrite, never a period.
```

### Vocabulary: durable 2026 markers (density-scored)

The 2023-24 list (delve, tapestry, realm) is decaying because humans now avoid those words. The durable markers are common words LLMs over-select at 2-5x human rate across GPT-5.5, Claude 4.8 and Gemini 3.1 (Kobak Sci Adv 2025; Wu et al 2026). They are ordinary English, so one per paragraph is fine. Three in a paragraph is a signature.

```python
STRICT_VOCAB_2026 = {
    # word / stem      : preferred replacement when the paragraph is over threshold
    "significant":      "<a number>",         # "significant growth" → "31% growth". Ask if no number exists.
    "crucial":          "<delete or 'the'>",  # "the crucial point is" → "the point is"
    "notably":          "",                   # delete + comma
    "particularly":     "",                   # delete
    "comprehensive":    "full",
    "insights?":        "<what was learned>", # "key insights" → say the thing
    "robust":           "solid",              # keep if it is a term of art (statistics, engineering)
    "leverag(e|es|ed|ing)": "use",
    "foster(s|ed|ing)?": "build",
    "landscape":        "field",
    "nuanced":          "specific",
    "multifaceted":     "<delete>",
    "holistic":         "full",
    "streamlin(e|es|ed|ing)": "simplify",
    "elevat(e|es|ed|ing)":    "improve",
    "empower(s|ed|ing)?":     "let",
    # older corporate verbs still worth counting (weaker signal, but readers still cite them)
    "utiliz(e|es|ed|ing)":    "use",
    "facilitat(e|es|ed|ing)": "help",
    "harness(es|ed|ing)?":    "use",
    "unlock(s|ed|ing)?":      "find",
    "navigat(e|es|ed|ing)":   "handle",
    "seamless":               "smooth",
    "ecosystem":              "space",
}

STRICT_ADVERB_FILLER = {
    # counted as markers; delete whole word + surrounding comma when the paragraph is over threshold
    "fundamentally", "essentially", "ultimately", "crucially", "notably",
    "arguably", "certainly", "definitely", "undoubtedly", "particularly",
}
```

### Grammar markers (density-scored; the 2026 structural signature)

```python
GRAMMAR_MARKERS = {
    # Present-participial clause openers: 5.3x human rate (PNAS 2025).
    # "Leveraging our data, we..." / "Building on this, ..." / "Recognizing that X, ..."
    "ing_opener": r"(?m)^[\s>*\-]*[A-Z][a-z]+ing\b[^.]{0,60},",
    # Nominalisations: verb-turned-noun that hides the actor.
    # "the implementation of" / "the utilization of" / "the optimization of"
    "nominalisation": r"\bthe (\w+(?:tion|sion|ment|ance|ence|ization|isation)) of\b",
    # Stacked abstract nouns
    "abstract_stack": r"\b(alignment|transformation|optimization|innovation|efficiency|scalability|synergy)\b.{0,40}\b(alignment|transformation|optimization|innovation|efficiency|scalability|synergy)\b",
}
# Fix for ing_opener: put the actor first. "Leveraging our data, we cut churn" → "We cut churn with our data."
# Fix for nominalisation: use the verb. "the implementation of the new flow" → "when we implemented the new flow"
```

### 2026 LinkedIn layer (density-scored)

Words and phrases that were human LinkedIn idiom in 2024 and are model idiom in 2026. Each counts as one marker; the phrases in the second block are scrubbed on a single hit because they are also reach-negative.

```python
LINKEDIN_LAYER_2026 = [
    r"\bquietly\b",                          # "quietly shipped", "quietly became"
    r"\b\w+ matters\b\.?",                   # "distribution matters." as a sentence
    r"\bcompound(s|ing)?\b",                 # "small wins compound"
    r"\ba signal\b|\bthe signal\b",
    r"\bthe work\b",                         # "do the work", "the work is the work"
    r"\bbuilt different\b",
    r"\bload-bearing\b",
    r"\bdoing the heavy lifting\b",
    r"\blet that sink in\b",
    r"\bthat's the real story\b",
]
```

### Reveal bridges (single hit = replace; measured reach-negative on LinkedIn)

```python
REVEAL_BRIDGES = [
    (r"(?m)^The (result|outcome|answer|lesson|catch|kicker|truth)\?\s*", ""),   # "The result?" -4.8% reach
    (r"(?i)\bit'?s not \w[^,.]{0,40}, it'?s \b", None),                          # "It's not X, it's Y" -4.9%; rewrite as paired declaratives
    (r"(?i)^stop \w[^,.]{0,40}\. start \b|^stop \w[^,.]{0,40}, start \b", None),  # "Stop X, start Y" -6.7%
    (r"(?im)^here'?s (what|how|why|the thing)\b[^:.\n]{0,40}[:.]\s*", ""),      # "Here's what/how" -4.3%
    (r"(?im)^(plot twist|spoiler|the twist)[:?]\s*", ""),
]
# Vendor data (single platform, 2026). Confidence: vendor. The direction is consistent with reader-tell reports.
# Fix: delete the bridge and let the next sentence stand. It was the point anyway.
```

### Negative parallelism (full coverage per 2026-04-27 ban; now also -4.9% reach)

```python
NEG_PARALLEL_PATTERNS = [
    # All forms must be rewritten as paired declaratives
    r"It's not just (\w+(?:\s+\w+){0,5}), it's (\w+(?:\s+\w+){0,5})",
    r"(\w+(?:\s+\w+){0,3}) isn't (\w+(?:\s+\w+){0,5}), it's (\w+(?:\s+\w+){0,5})",
    r"Not (\w+(?:\s+\w+){0,5}), but (\w+(?:\s+\w+){0,5})",
    r"It's not about (\w+(?:\s+\w+){0,5}), it's about (\w+(?:\s+\w+){0,5})",
    r"The question isn't (\w+(?:\s+\w+){0,5}), it's (\w+(?:\s+\w+){0,5})",
    r"This isn't (\w+(?:\s+\w+){0,5})\. This is (\w+(?:\s+\w+){0,5})",
    r"The real (\w+) isn't (\w+(?:\s+\w+){0,5}), it's (\w+(?:\s+\w+){0,5})",
]

# Replacement strategy: rewrite as paired declaratives, NOT as auto-substitution.
# Example:
#   "the bet isn't unit economics, it's owning distribution"
#   → "nobody's playing for unit economics. they're playing to own distribution."
# Always flag for user review since meaning preservation needs human judgment.
```

### Rule of three (strict at density; one natural triad is allowed)

Tricolon runs at 2x expert-human density across 2026 frontier models (arXiv 2604.19768). The tell is the stacked or perfectly parallel triad and the repeat, not the form: 26% of top human tweets contain exactly one.

```python
def detect_triads(text: str) -> list:
    patterns = [
        r"(\w+), (\w+),? and (\w+)",                       # word triplets
        r"(\w+ \w+), (\w+ \w+),? and (\w+ \w+)",           # short-phrase triplets
        r"(?m)^(\w+)\. (\w+)\. (\w+)\.$",                  # "Simple. Effective. Easy." (also a Pass 2 staccato hit)
        r"\b(no \w+)[,.] (no \w+)[,.] (just|only) \w+",    # "No X. No Y. Just Z." (also a Pass 2 hit)
    ]
    return [m for p in patterns for m in re.finditer(p, text, flags=re.I)]

def triad_action(triads: list, text: str) -> list:
    """STRICT: scrub any triad whose three items are interchangeable or perfectly parallel
    (same part of speech, same length, no receipts), and every triad beyond the second in a post.
    Leave ONE natural triad with concrete, non-interchangeable items.
    AESTHETIC: scrub the last remaining one too."""
    actions = []
    for i, t in enumerate(triads):
        items = t.groups()
        parallel = len(set(len(x.split()) for x in items)) == 1
        hollow = all(x.lower() in HOLLOW_ADJECTIVES for x in items) if len(items) == 3 else False
        if parallel or hollow or i >= 2:
            actions.append((t, "REWRITE_AS_TWO_OR_FOUR"))   # 2 items, or 4 with one that breaks the pattern
        else:
            actions.append((t, "LEAVE"))
    return actions

HOLLOW_ADJECTIVES = {"dynamic", "vibrant", "innovative", "faster", "cheaper", "better", "simple",
                     "effective", "easy", "bold", "clear", "focused", "scalable", "powerful"}
```

### Phrase-level cleanup

```python
STRICT_PHRASES = [
    (r"\bIn today's fast-paced world[,.]?\s*", ""),
    (r"\bin the age of AI[,.]?\s*", ""),
    (r"\bat the end of the day[,.]?\s*", ""),
    (r"\bgame-changer\b", "unusual"),
    (r"\bdeep dive\b", "look"),
    (r"\bneedle-moving\b", "real"),
    (r"\bmove the needle\b", "change the numbers"),
    (r"\bparadigm shift\b", "real shift"),
    (r"\bpivotal moment\b", "the moment"),
    (r"\btestament to\b", "shows"),
    (r"\btapestry of\b", "set of"),
    (r"\bin a world where\b", "when"),
    (r"\bthe (harsh|hard|uncomfortable) (truth|reality) is\b[:,]?\s*", ""),
]
```

---

## TIER: AESTHETIC (opt-in only)

Patterns AI uses but humans use legitimately, plus the 2023-24 vocabulary that is now decaying and mostly harmless. Apply only when audience demands it. Will flatten literary writing and will trip the Pass 4 guard.

### Aesthetic vocabulary (decaying 2023-24 set + defendable normal English)

```python
AESTHETIC_VOCAB_REPLACE = {
    # Decaying 2023-24 markers. Humans now avoid them, so a single instance reads as human-ish.
    # Still counted as ONE marker each in score_paragraph() at strict; replaced outright only at aesthetic.
    "delve":       "look",
    "delving":     "looking",
    "tapestry":    "set",
    "realm":       "area",
    "intricate":   "complex",
    "intricacies": "details",
    "journey":     "<the actual thing: the year, the project, the 14 months>",
    "paradigm":    "approach",
    # Defendable normal English. Every epidemiologist, scientist, novelist uses these.
    "cultivate":   "grow",
    "vibrant":     "alive",                  # Toni Morrison Nobel lecture
    "garner":      "get",
    "showcase":    "show",
    "underscore":  "show",
    "highlight":   "show",                   # only when used as filler verb, not noun
    "bolster":     "back",
    "bolstered":   "backed",
    "meticulous":  "careful",
    "valuable":    "useful",
}
```

### Em dashes (aesthetic: scrub the last one too)

```python
# Strict leaves ~1 per 100 words. Aesthetic removes the remaining one(s) for audiences that
# treat any dash as suspicious (some academic forums). Even here: comma / colon / parentheses,
# never a period. Know that zero dashes in a 300-word post is itself below the human baseline.
AESTHETIC_PUNCT_STRIP = [
    (r"\s*—\s*", ", "),
    (r"–", "-"),
]
```

### Rule of three (the last natural one)

```python
# Strict leaves one natural triad per post. Aesthetic breaks it into 2 or 4 items.
# Defense: Lincoln, Caesar, Churchill. Apply only when the audience hunts for tells.
```

### Passive voice

```python
# Defense: scientific writing, news leads, legal writing all require passive.
# Watson & Crick 1953 paper opens passive: "It has not escaped our notice..."
# Joan Didion: "The center was not holding."
PASSIVE_TARGETS = [
    r"was (\w+ed) by",
    r"is being (\w+ed)",
    r"has been (\w+ed)",
    r"will be (\w+ed)",
]
```

---

## Pass 2 — Rhythm restoration (all tiers)

Replaces V2's `enforce_burstiness()`. Detectors do not score burstiness (GPTZero dropped it in 2023). On LinkedIn, sentence-length variance is not an engagement lever in either direction: our author-normalised corpus (keyword n=205 + top-creator n=192, 2026-09) shows within-creator ratios of 0.96 / 0.80 / 0.92 across length bands, Spearman -0.06, and a mild uniform-rhythm advantage for one-idea-per-line posts at 112-204 words. The earlier X/Threads finding ("bursty wins on long posts") was an author confound and does not transfer. What readers do notice is machine-flat uniformity (structure = 36% of expert judgments) and, worse, staged variance: mechanical long/short alternation is a learnable humanizer fingerprint (DAMAGE 2025). So: fix rhythm only where it reads machine-flat, remove manufactured variance everywhere, never add variance as a tactic.

```python
STACCATO_TELLS = [
    r"(?m)^\w+\.$",                                              # one-word paragraph: "Still." "Mostly." "Exactly."
    r"(?m)^(\w+\. ){2,}\w+\.$",                                  # "Short. Punchy. Done." / "Simple. Effective. Easy."
    r"(?i)\bno \w+\. no \w+\. (just|only) \w+",                  # "No X. No Y. Just Z."
    r"(?i)\ball (of )?the \w+\. none of the \w+",                # "All the X. None of the Y."
    r"(?m)^The (result|outcome|answer|lesson|catch|kicker|truth)\?",  # "The result?" reveal (also strict reveal bridge)
    r"(?i)\b(why|how|what happened)\? (because|simple|easy)\b",  # pseudo-Socratic Q&A
    r"(?i)\b(that's it|that's all|that's the post|full stop|period)\.$",
]

def restore_rhythm(text: str) -> str:
    """V3. Remove staged variance; un-flatten only what reads machine-flat. Never manufacture variance."""
    paragraphs = split_paragraphs(text)
    fragments_seen = 0

    for i, p in enumerate(paragraphs):
        # 1. Kill staged rhythm first. Merge staccato runs into one full sentence with a real clause.
        for pat in STACCATO_TELLS:
            if re.search(pat, p):
                p = merge_into_sentence(p, pat)     # "No meetings. No decks. Just code." → "We skipped the meetings and the decks and shipped code."

        sents = split_sentences(p)
        lengths = [len(s.split()) for s in sents]

        # 2. Cap standalone fragments (<4 words) at 2 per POST, not per paragraph.
        for j, n in enumerate(lengths):
            if n < 4:
                fragments_seen += 1
                if fragments_seen > 2:
                    sents[j] = attach_to_neighbor(sents, j)   # fold into the previous sentence with a comma or colon

        # 3. Un-flatten ONLY a machine-flat paragraph: 4+ sentences, every one within ±3 words of the
        #    mean, no subordinate clause anywhere. Then extend the ONE sentence that carries the most
        #    content by joining it to its natural neighbour with a clause that does work (because / which /
        #    when / after), not a comma splice. Once per paragraph, and only if the result reads like the
        #    author. A paragraph with one long and one short sentence is already fine. Two or three
        #    mid-length sentences in a row are fine. This is not a reach tactic: on LinkedIn sentence-length
        #    variance is null-to-slightly-negative for engagement; the only goal is to not read machine-flat.
        if len(sents) >= 4 and all(abs(n - mean(lengths)) <= 3 for n in lengths) and not any(has_working_clause(s) for s in sents):
            k = argmax(lengths)
            sents[k] = join_with_clause(sents[k], sents[k + 1] if k + 1 < len(sents) else sents[k - 1])

        # 4. Never long/short/long/short across the post. If the paragraph now alternates, fold the
        #    second short sentence back in. The seesaw is the humanizer fingerprint.

        # 5. One-idea-per-line posts (112-204 words, each paragraph one sentence): leave rhythm alone entirely.
        #    Uniform rhythm has a mild advantage in that format on LinkedIn.

        paragraphs[i] = " ".join(sents)

    return "\n\n".join(paragraphs)
```

Layout vs rhythm: 1-2 sentence paragraphs with blank lines between them are LinkedIn's mobile-native layout and are **not** touched by this pass. A paragraph that is one full 22-word sentence is layout. A paragraph that is "Still." is fragment-for-drama. The pass edits sentences, never the blank lines.

Length note: on LinkedIn our corpus shows sentence-length variance is not an engagement lever (null-to-slightly-negative within-creator); the short-form "don't force variance" rule applies to sibling platforms (Threads, short X). Here it applies at every length.

## Pass 3 — Forbidden insertions (sincerity markers, hedges)

Pass 3 adds concreteness only (a referenced odd-precision number, a named entity, a flat dated fact). It never adds these, and Pass 1 strict removes them when the draft already has them as an opener or pivot:

```python
SINCERITY_MARKERS = [
    r"(?im)^(let me be (honest|real|direct|clear)|i'?ll be (honest|real|direct)|honestly\?|honest (caveat|version|answer)|the honest (version|answer|truth) is|to be (direct|honest|fair|transparent)|real talk|full transparency|can i be (honest|vulnerable)|i'?ll say the quiet part|not gonna lie|ngl|unpopular opinion)[:,.]?\s*",
    r"(?i)\b(i (might|may|could) be wrong,? but|perhaps|it seems (to me )?that|in my humble opinion|i think it'?s fair to say)\b",  # inserted hedges: only scrub if NOT in the author's voice samples
]
# Fix: delete the marker and keep the sentence that follows. If the sentence that follows is not
# a specific fact, the marker was doing the work of vulnerability. Ask the author for the fact.
# Evidence: performed hesitancy 2x more common in LLM than expert human text; confession-cue humanizers
# caught 100% by expert readers; "false vulnerability" is a named 2026 tell (tropes.fyi).
# A flat dated uncomfortable fact with no frame is reach-POSITIVE (+4.6% to +10%, vendor data).
```

## Cliché opener / closer detection (strict tier)

```python
OPENER_TELLS = [
    r"^In today's ",
    r"^Have you ever ",
    r"^Most people don't realize ",
    r"^Here's a hard truth",
    r"^Let me tell you about ",
    r"^Here's (what|how|why) ",               # reveal bridge as opener
    r"^(Stop|Quit) \w+ing\b.*\b(start|try)\b", # "Stop X, start Y"
]

CLOSER_TELLS = [
    r"What do you think\?",
    r"Thoughts\?",
    r"Agree or disagree\?",
    r"Let me know in the comments",
    r"Tag someone who needs this",
    r"Smash the like button",
    r"Let that sink in\.?$",
    r"That's the real story\.?$",
    r"(?m)^\w+\.$\Z",                         # one-word closing paragraph
]
```

## Preserve these (user voice, don't scrub)

- Lowercase sentence starts (Serge's signature)
- `..` as soft pause (not em dash)
- One or two sentence fragments used intentionally ("Worth it.", "Every time.") - the cap is 2 per post, not 0
- One em dash per ~100 words. Do not push the count to zero; zero is below the human baseline
- One natural rule-of-three with concrete, non-interchangeable items
- One genuinely long sentence per paragraph, even if a style guide would split it
- Contractions (don't, it's, you're)
- Specific numbers with referents and named entities (add MORE, never remove)
- First-person sensory details
- The author's reactions and opinions, including a blunt one. Flat tone across a whole post is a humanizer fingerprint
- A single common-word marker in a paragraph ("notably", "robust" as a term of art). One is not a verdict

## Comment-reply scrub (when replying to commenters on your own post)

**Forbidden author replies** (signal low quality, downrank the thread):

- "Great point!"
- "Thanks!"
- "100%"
- "Well said."
- "🙌"
- "So true."

**Required:** every author reply must contain at least one of:
- A new concrete detail not in the original post
- A specific name (person, company, tool)
- A follow-up question that invites thread depth

## Announcement-opener scrub (strict tier)

Replace these patterns with the concrete moment that prompted the post:

- "I'm excited to announce" → describe what actually happened, in order
- "I'm thrilled to share" → just share it, no preamble
- "Honored to be mentioned" → what did you do to earn the mention?
- "Delighted to be featured" → lead with the insight, not the feature
- "Let me be honest" / "I'll be real" → delete the announcement; state the dated fact that follows it, flat
