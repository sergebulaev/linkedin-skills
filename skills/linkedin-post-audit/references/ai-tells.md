# AI Tells — Complete Blacklist

## Punctuation (regex)

| Pattern | Why | Fix |
|---|---|---|
| `\u2014` (em dash `—`) | Biggest AI tell. GPTZero + OriginalityAI flag instantly | Replace with `.` or `,` |
| `\u2013` (en dash `–`) | Same | Replace with `-` or `to` |
| `--` | Same family | Replace with `.` or `,` |
| `\u201C\u201D` (curly quotes) | Copy-paste artifact | Convert to `"` |

## Vocabulary blacklist

Delete every instance. These are high-probability AI markers:

**Verbs:** leverage, utilize, facilitate, streamline, delve, navigate, unlock, harness, foster, cultivate

**Adverbs:** fundamentally, essentially, ultimately, crucially, notably

**Nouns:** landscape, ecosystem, paradigm, realm, tapestry, journey

**Adjectives:** robust, seamless, holistic, nuanced

## Phrase blacklist

- "It's not just X, it's Y" (inflated parallel construction)
- "In today's fast-paced world"
- "Game-changer"
- "Deep dive"
- "Needle-moving"
- "Move the needle"
- "At the end of the day"
- "When it comes to"
- "In the age of AI"
- "Paradigm shift"

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

- Every sentence 15-22 words (uniform rhythm)
- Every paragraph 3 lines
- Perfect parallel structure across a list
- Hedging stacks: "perhaps", "might", "could potentially", "it seems"
- Passive voice >10% of clauses
- Triple-listing everything ("faster, cheaper, better")

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
AI_PATTERNS = {
    "em_dash": r"\u2014",
    "en_dash": r"\u2013",
    "double_dash": r"--",
    "vocab": r"\b(leverage|utilize|facilitate|streamline|delve|navigate|unlock|harness|foster|cultivate|fundamentally|essentially|ultimately|crucially|notably|landscape|ecosystem|paradigm|realm|tapestry|robust|seamless|holistic|nuanced)\b",
    "opener_filler": r"^(In today's|Have you ever|Most people don't realize|Here's a hard truth)",
    "closer_filler": r"(What do you think\?|Thoughts\?|Agree or disagree\?|Let me know in the comments|Tag someone)",
    "inflated_symbolism": r"not just \w+, it's \w+",
}
```
