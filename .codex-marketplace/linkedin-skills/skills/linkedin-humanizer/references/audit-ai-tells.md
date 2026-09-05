# AI Tells — Complete Blacklist (V3, 2026-09)

Scored the way readers read: by density per paragraph, not per word. One marker in a paragraph is English. Three is a signature. The exceptions that fail on a single hit are listed as such.

## Contents

- Punctuation (regex)
- Vocabulary markers (density-scored)
- Phrase blacklist (single hit)
- Opening-line tells
- Closing-line tells
- Structural tells
- 2026 dos-and-donts blockers (auto-fail)
- Attention budget
- Regex patterns (for audit implementation)

## Punctuation (regex)

| Pattern | Why | Fix |
|---|---|---|
| `\u2014` (em dash `—`) above ~1 per 100 words (1-2 per post) | Density tell, not a character tell. GPT-5.4 uses fewer than humans; 23% of top-creator LinkedIn posts contain one (author-relative ratio 1.09, not a tell). 3+ in a short post is the old GPT-4 glue habit | Replace only the excess: `,` or `:` or `( )` or a rewrite. Never `.` (fragment stacking is worse) |
| `\u2014` at zero across a 300+ word post that reads as if it wanted one | Below the human baseline; reads as dash self-censoring | Leave one in |
| `\u2013` (en dash `–`) between clauses | Same family | Replace with `,`; number ranges stay |
| `--` | Same family | Replace with `,` or rewrite |
| `\u201C\u201D` (curly quotes) | Copy-paste artifact | Convert to `"` |

## Vocabulary markers (density-scored)

Count per paragraph. **3+ = rewrite the paragraph. 2 = replace the weakest. 1 = leave it.** AI vocabulary is the one marker that is consistently reach-negative on LinkedIn in our own corpus (0.74-0.84 author-relative), so this pass stays even though the word list changed.

**Durable 2026 set (common words, 2-5x human rate across GPT-5.5 / Claude 4.8 / Gemini 3.1):** significant, crucial, notably, particularly, comprehensive, insights, robust, leverage, foster, landscape, nuanced, multifaceted, holistic, streamline, elevate, empower

**Older corporate verbs (weaker but still cited by readers):** utilize, facilitate, harness, unlock, navigate, seamless, ecosystem

**Filler adverbs:** fundamentally, essentially, ultimately, crucially, notably, particularly

**Grammar markers:** sentence-opening "-ing" clause ("Leveraging our data, we..."), nominalisation ("the implementation of"), stacked abstract nouns (alignment / transformation / optimization / synergy)

**2026 LinkedIn layer:** quietly, "X matters." as a sentence, compound(s), "a signal", "the work", "built different", load-bearing, "doing the heavy lifting", "let that sink in", "that's the real story"

**Decaying 2023-24 set (count as one marker each, but do not chase in isolation):** delve, tapestry, realm, intricate, journey, paradigm, cultivate

## Phrase blacklist (single hit = fix)

Reveal bridges and negative parallelism are scrubbed on one hit because they are reach-negative on LinkedIn (vendor data, 2026):

- "The result?" / "The catch?" / "The kicker?" (-4.8%)
- "It's not just X, it's Y" and all 6 negative-parallelism forms (-4.9%)
- "Stop X, start Y" (-6.7%)
- "Here's what / Here's how / Here's the thing" (-4.3%)
- "In today's fast-paced world"
- "Game-changer"
- "Deep dive"
- "Needle-moving"
- "Move the needle"
- "At the end of the day"
- "When it comes to"
- "In the age of AI"
- "Paradigm shift"
- "The hard truth is" / "The uncomfortable reality is"
- Sincerity announcements as opener or pivot: "let me be honest", "I'll be real", "honestly?", "to be direct", "the honest version is", "honest caveat", "real talk", "full transparency", "unpopular opinion:"

## Opening-line tells

- Any sentence starting with "In today's..."
- Rhetorical question hooks ("Have you ever wondered...?") — dead on LinkedIn
- All-caps first line ("THIS CHANGED EVERYTHING.")
- "Most people don't realize..."
- "Here's a hard truth..."

## Closing-line tells

- "What do you think?"
- "Thoughts?"
- "Agree or disagree?"
- "Let me know in the comments!"
- "Tag someone who needs this."

## Structural tells

- Every sentence the same length, machine-flat (expert readers cite structure 36% of the time). Fix only where it reads flat; on LinkedIn sentence-length variance is not a reach lever in either direction (our corpus, within-creator: null to slightly negative), so never manufacture it
- Staccato stacks: "Short. Punchy. Done.", "Simple. Effective. Easy.", "No X. No Y. Just Z.", "All the X. None of the Y."
- One-word paragraphs ("Still." "Mostly." "Exactly.")
- More than 2 standalone fragments (<4 words) in the post
- Long/short/long/short seesaw across the whole post (mechanical alternation is a humanizer fingerprint)
- Pseudo-Socratic Q&A ("Why? Because...")
- Every paragraph 3 lines
- Perfect parallel structure across a list
- Stacked or perfectly parallel triads, or 3+ triads in one post ("faster, cheaper, better"). One natural triad is fine
- Hedging stacks: "perhaps", "might", "could potentially", "it seems" (performed hesitancy runs 2x human rate)
- Framed confession: a sincerity sentence wrapped around a fact ("I'll be honest, this hurt: we lost the client"). The fact alone is fine
- Passive voice >10% of clauses
- Uniformly flat tone with no reaction, no opinion, no concrete detail (the over-scrubbed fingerprint)

## 2026 dos-and-donts blockers (auto-fail)

| Pattern | Why | Fix |
|---|---|---|
| External link in post body | -40 to -60% reach penalty; LinkedIn suppresses off-platform traffic | Move link to first comment, or summarize the insight inline |
| "Comment YES if you agree" / "Drop a 🙌" / manufactured CTA | Algorithm explicitly detects and demotes engagement bait | Ask a specific open question tied to the post's thesis |
| Press-release / corporate-polished tone | Underperforms personal voice 3x; suppresses authenticity signals | Rewrite in first person with a concrete moment |
| Humble-brag opener ("honored to announce…") | Failures outperform humble brags **8.5x** | Lead with what broke or what you learned |
| Significant edits within first hour of posting | Resets the algorithm's initial distribution test | Fix typos only in first 60 min; hold structural edits |
| Posts >3x/week from one author | Diminishing returns; cannibalizes own reach | Cap at 2-3x/week, same time/days |
| Company-page-only distribution | Employee posts get 6-8x more reach than company pages | Publish from personal profile, let company reshare |
| Pure vanity-metric chasing (likes only) | Likes are weakest signal; saves > comments > shares > likes | Design for saves: frameworks, templates, data |
| Announcement openers ("I'm excited to share") | Reads as PR; kills voice | Replace with the concrete moment that prompted the post |

## Attention budget

Average user screen attention is **47 seconds** (down from 150 seconds in 2004). Post dwell-time target: 31-60 seconds.

Flag any draft that demands >60s of continuous reading without a visual break, list, or fragment sentence — it'll lose the skim layer.

## Regex patterns (for audit implementation)

```python
import re

# Verb stems that should match every inflection (-s, -ing, -ed, -es).
# Use a non-capturing inflection suffix so "harnessed", "fostering", "unlocks" all match.
_VERB_STEMS = (
    "leverag", "utiliz", "facilitat", "streamlin", "delv", "navigat",
    "unlock", "harness", "foster", "cultivat", "elevat", "empower",
)
_VERB_GROUP = "|".join(_VERB_STEMS)

# DENSITY-SCORED markers: count hits per paragraph. 3+ = rewrite paragraph, 2 = replace weakest, 1 = leave.
DENSITY_PATTERNS = {
    "vocab_verbs": rf"\b(?:{_VERB_GROUP})(?:e|es|ed|ing|s)?\b",
    "vocab_2026": r"(?i)\b(significant(ly)?|crucial(ly)?|notably|particularly|comprehensive|insights?|robust|landscape|nuanced|multifaceted|holistic|seamless|ecosystem)\b",
    "adverb_filler": r"(?i)\b(fundamentally|essentially|ultimately|arguably|certainly|definitely|undoubtedly)\b",
    "ing_opener": r"(?m)^[\s>*\-]*[A-Z][a-z]+ing\b[^.\n]{0,60},",
    "nominalisation": r"(?i)\bthe \w+(?:tion|sion|ment|ance|ence|ization|isation) of\b",
    "linkedin_2026": r"(?i)\b(quietly|compound(s|ing)?|(a|the) signal|the work|built different|load-bearing|doing the heavy lifting)\b|(?m)^\w+ matters\.$",
    "decaying_2024": r"(?i)\b(delve|delving|tapestry|realm|intricate|journey|paradigm)\b",
}

# SINGLE-HIT patterns: one match = fix.
AI_PATTERNS = {
    "en_dash": r"\u2013",
    "double_dash": r"--",
    # Reveal bridges (reach-negative on LinkedIn).
    "reveal_bridge": r"(?im)^(the (result|outcome|answer|lesson|catch|kicker|truth)\?|here'?s (what|how|why|the thing)\b|stop \w+[^.\n]{0,40}[.,] ?start \b|plot twist:)",
    "inflated_symbolism": r"(?i)not just \w+, it'?s \w+",
    "neg_parallel": r"(?i)\b(isn'?t|not) (about )?[^,.\n]{1,40}, it'?s (about )?\b",
    # Staccato / forced rhythm.
    "staccato_stack": r"(?m)^(\w+\. ){2,}\w+\.$",
    "one_word_paragraph": r"(?m)^\w+\.$",
    "no_no_just": r"(?i)\bno \w+\. no \w+\. (just|only) \w+",
    "all_none": r"(?i)\ball (of )?the \w+\. none of the \w+",
    "pseudo_socratic": r"(?i)\b(why|how)\? (because|simple)\b",
    # Sincerity announcements as opener or pivot.
    "sincerity_marker": r"(?im)^[\s>*\-]*(let me be (honest|real|direct|clear)|i'?ll be (honest|real|direct)|honestly\?|honest (caveat|version|answer)|the honest (version|answer|truth) is|to be (direct|honest|transparent)|real talk|full transparency|can i be (honest|vulnerable)|not gonna lie|ngl|unpopular opinion)\b",
    # Case-insensitive opener match; allow leading whitespace, bullets, or quote marks.
    "opener_filler": r"(?im)^[\s>*\-]*[\"'\u201c]?(In today's|Have you ever|Most people don't realize|Here's a hard truth)",
    # Generic closing-question CTA: matches "What do you think?" / "What are your thoughts?" / "Thoughts?" / "Your take?" etc.
    "closer_filler": r"(?i)(what (do|are) you (think|your? thought)|what(?:'s| is) your (take|thoughts?)|thoughts\?|agree or disagree\?|let me know in the comments|tag someone|let that sink in|that'?s the real story)",
}

def em_dash_excess(text: str) -> int:
    """Em dashes above the cap (~1 per 100 words, floor 1, ceiling 2 per post). 0 = fine."""
    words = len(text.split())
    cap = max(1, min(2, round(words / 100)))
    return max(0, text.count("\u2014") - cap)

def fragment_count(text: str) -> int:
    """Standalone sentences under 4 words. More than 2 per post = forced rhythm."""
    return sum(1 for s in re.split(r"(?<=[.!?])\s+", text) if 0 < len(s.split()) < 4)

def paragraph_density(paragraph: str) -> int:
    return sum(len(re.findall(p, paragraph)) for p in DENSITY_PATTERNS.values())

# Compile-time sanity: catches inflected and conjugated forms.
assert re.search(DENSITY_PATTERNS["vocab_verbs"], "We harnessed cross-functional synergy.")
assert re.search(DENSITY_PATTERNS["vocab_verbs"], "We fostered alignment.")
assert re.search(DENSITY_PATTERNS["vocab_verbs"], "We unlocked 47% gains.")
assert re.search(DENSITY_PATTERNS["ing_opener"], "Leveraging our data, we cut churn.")
assert re.search(AI_PATTERNS["closer_filler"], "What are your thoughts?")
assert re.search(AI_PATTERNS["closer_filler"], "What's your take?")
assert re.search(AI_PATTERNS["reveal_bridge"], "The result? We doubled.")
assert re.search(AI_PATTERNS["no_no_just"], "No meetings. No decks. Just code.")
assert re.search(AI_PATTERNS["sincerity_marker"], "Let me be honest: this one hurt.")
assert em_dash_excess("a \u2014 b " * 3 + "word " * 90) == 2
assert em_dash_excess("one \u2014 dash in " + "word " * 120) == 0
```
