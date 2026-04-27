# Scrub Rules — V2 Tiered (Regex + Replacements)

V2 (2026-04-27): rules split into **forensic / strict / aesthetic** tiers. See SKILL.md for tier philosophy.

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

### Em dash OVERUSE (3+ in <300 word post)

```python
def detect_em_dash_overuse(text: str) -> bool:
    """Flag if 3+ em dashes in posts under 300 words.
    Single use is aesthetic-tier. Three+ is forensic."""
    word_count = len(text.split())
    em_count = text.count("—")
    if word_count < 300 and em_count >= 3:
        return True
    return False
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

Corporate-speak. Bad LinkedIn style regardless of who wrote it. Easy to defend the ban.

### Punctuation

```python
STRICT_PUNCT = [
    (r"“|”", '"'),                # curly quotes → straight
    (r"‘|’", "'"),                # curly apostrophes → straight (preserve apostrophe-in-contractions: don't / it's / you're)
    (r"--", ". "),                           # double dash → period
]
```

### Vocabulary (strip and replace)

```python
STRICT_VOCAB_REPLACE = {
    # corporate verbs (no human-writer defense)
    "leverage": "use",
    "leveraging": "using",
    "leveraged": "used",
    "utilize": "use",
    "utilizing": "using",
    "utilized": "used",
    "facilitate": "help",
    "facilitating": "helping",
    "streamline": "simplify",
    "streamlining": "simplifying",
    "delve": "look",
    "delving": "looking",
    "navigate": "handle",
    "navigating": "handling",
    "unlock": "find",
    "unlocking": "finding",
    "unlocked": "found",
    "harness": "use",
    "harnessing": "using",
    # corporate nouns
    "landscape": "field",
    "ecosystem": "space",
    "paradigm": "approach",
    "realm": "area",
    # corporate adjectives
    "seamless": "smooth",
    "holistic": "full",
    "nuanced": "specific",
}

STRICT_VOCAB_DELETE = {
    # filler adverbs — delete whole word + surrounding comma
    "fundamentally", "essentially", "ultimately", "crucially", "notably",
    "arguably", "certainly", "definitely", "undoubtedly",
}
```

### Negative parallelism (full coverage per 2026-04-27 ban)

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
]
```

---

## TIER: AESTHETIC (opt-in only)

Patterns AI uses but humans use legitimately. Apply only when audience demands it. Will flatten literary writing.

### Aesthetic vocabulary (defendable normal English)

```python
AESTHETIC_VOCAB_REPLACE = {
    # The defense: every epidemiologist, scientist, novelist uses these.
    "robust": "solid",                       # Used in epidemiology since 1950s
    "foster": "build",                       # George Eliot used "cultivate" in Middlemarch
    "cultivate": "grow",
    "vibrant": "alive",                      # Toni Morrison Nobel lecture
    "intricate": "complex",
    "intricacies": "details",
    "garner": "get",
    "showcase": "show",
    "underscore": "show",
    "highlight": "show",                     # only when used as filler verb, not noun
    "bolster": "back",
    "bolstered": "backed",
    "meticulous": "careful",
    "valuable": "useful",
}
```

### Em dashes (single use)

```python
# ONLY in aesthetic mode — Dickinson and McCarthy defense ignored
AESTHETIC_PUNCT_STRIP = [
    (r"—", ". "),                       # all em dashes → periods
    (r"–", "-"),                        # all en dashes → hyphens
]
```

### Rule of three

```python
def detect_rule_of_three(text: str) -> list:
    """Find triplet adjectives or triplet clauses.
    Defense: Lincoln, Caesar, Churchill all used this. Aesthetic-tier only."""
    patterns = [
        r"(\w+), (\w+), and (\w+)",           # adjective triplets
        r"(\w+ \w+), (\w+ \w+), and (\w+ \w+)",  # short-phrase triplets
    ]
    return [m for p in patterns for m in re.finditer(p, text)]
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

## Pass 2 — Burstiness enforcement (all tiers)

```python
def enforce_burstiness(text: str) -> str:
    """Break uniform 15-22 word sentences. Add fragments."""
    sentences = split_sentences(text)
    lengths = [len(s.split()) for s in sentences]
    avg = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)

    if variance < 25 and avg > 12:
        for i in range(2, len(sentences), 3):
            sentences[i] = shorten(sentences[i])

    return " ".join(sentences)
```

## Cliché opener / closer detection (strict tier)

```python
OPENER_TELLS = [
    r"^In today's ",
    r"^Have you ever ",
    r"^Most people don't realize ",
    r"^Here's a hard truth",
    r"^Let me tell you about ",
]

CLOSER_TELLS = [
    r"What do you think\?",
    r"Thoughts\?",
    r"Agree or disagree\?",
    r"Let me know in the comments",
    r"Tag someone who needs this",
    r"Smash the like button",
]
```

## Preserve these (user voice, don't scrub)

- Lowercase sentence starts (Serge's signature)
- `..` as soft pause (not em dash)
- Sentence fragments used intentionally ("Worth it.", "Every time.")
- Contractions (don't, it's, you're)
- Specific numbers and named entities (add MORE, never remove)
- First-person sensory details

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
