# Scrub Rules — Regex + Replacements

## Punctuation

```python
PUNCT_RULES = [
    (r"\u2014", ". "),           # em dash → period+space (or comma in some contexts)
    (r"\u2013", "-"),             # en dash → hyphen
    (r"--", ". "),                # double dash → period+space
    (r"\u201C|\u201D", '"'),      # curly quotes → straight
    (r"\u2018|\u2019", "'"),      # curly apostrophes → straight
]
```

## Vocabulary

```python
VOCAB_REPLACE = {
    # verbs
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
    "foster": "build",
    "fostering": "building",
    "cultivate": "grow",
    "cultivating": "growing",
    # nouns
    "landscape": "field",
    "ecosystem": "space",
    "paradigm": "approach",
    "realm": "area",
    # adjectives
    "robust": "solid",
    "seamless": "smooth",
    "holistic": "full",
    "nuanced": "specific",
}

VOCAB_DELETE = {
    # filler adverbs — delete whole word + surrounding comma if present
    "fundamentally", "essentially", "ultimately", "crucially", "notably",
    "arguably", "certainly", "definitely", "undoubtedly",
}
```

## Phrase-level

```python
PHRASE_REPLACE = [
    (r"\bIn today's fast-paced world[,.]?\s*", ""),
    (r"\bin the age of AI[,.]?\s*", ""),
    (r"\bat the end of the day[,.]?\s*", ""),
    (r"\bgame-changer\b", "unusual"),
    (r"\bdeep dive\b", "look"),
    (r"\bneedle-moving\b", "real"),
    (r"\bmove the needle\b", "change the numbers"),
    (r"\bparadigm shift\b", "real shift"),
    # "It's not just X, it's Y" — these need human rewrite, flag for user
    (r"It's not just (\w+), it's (\w+)", r"It's \2."),
]
```

## Structural rules (post-regex pass)

```python
def enforce_burstiness(text: str) -> str:
    """Break uniform 15-22 word sentences. Add fragments."""
    sentences = split_sentences(text)
    lengths = [len(s.split()) for s in sentences]
    avg = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)

    # If variance low (all sentences similar length), force-break
    if variance < 25 and avg > 12:
        # Break every 3rd sentence into shorter chunks
        for i in range(2, len(sentences), 3):
            sentences[i] = shorten(sentences[i])

    return " ".join(sentences)
```

## Cliché opener / closer detection

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
- `..` as soft pause (not `—`)
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

**Required:** every author reply must contain ≥1 of:
- A new concrete detail not in the original post
- A specific name (person, company, tool)
- A follow-up question that invites thread depth

## Announcement-opener scrub

Replace these patterns with the concrete moment that prompted the post:

- "I'm excited to announce" → describe what actually happened, in order
- "I'm thrilled to share" → just share it, no preamble
- "Honored to be mentioned" → what did you do to earn the mention?
- "Delighted to be featured" → lead with the insight, not the feature
