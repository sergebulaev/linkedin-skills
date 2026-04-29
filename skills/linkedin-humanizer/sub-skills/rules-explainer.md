# LinkedIn Rules Explainer

The educational backbone for the humanizer package. Every rule in `linkedin-humanizer` came from somewhere — Wikipedia's "Signs of AI writing" taxonomy, OriginalityAI's heuristics, GPTZero's stylometry, or 2026 LinkedIn-specific patterns. Some are real forensics (a `[oaicite:0]` marker is undefendable). Some are corporate-speak bans the user wants out for taste reasons. Some are aesthetic overreach — patterns Lincoln, Dickinson, and Didion built careers on, now flagged because GPT-4 happens to use them too.

This skill answers a simple question: **for any given rule, is the AI-tell verdict forensic, strict, or aesthetic — and how strong is the defense?**

## When to use

- Defending a stylistic choice that a detector flagged ("but Emily Dickinson uses em dashes")
- Arguing the controversial post about AI-rule overreach
- Auditing humanizer output before applying a rewrite
- Teaching a team which rules are real signals vs which are taste calls
- Reviewing a false positive from OriginalityAI / GPTZero / Pangram

## Input

Either:
- A specific rule name ("em dashes", "rule of three", "robust")
- A flagged passage from a detector
- A request to walk the full taxonomy

## Output

For each rule:
- **The rule** (what gets flagged)
- **Tier** (forensic / strict / aesthetic)
- **One-line summary** (why it's flagged)
- **Famous human writer** who uses this pattern (with example)
- **Defense strength** (low / medium / high)
- **Citation** (when available)

## The three tiers

### Forensic — real AI signals, undefendable

These are leakage from the model itself or the prompt template. No human writer ever produces them by accident. If the humanizer flags one, accept the rewrite.

Examples: `oaicite` markers, `contentReference` tokens, `turn0search0` artifacts, knowledge-cutoff disclaimers ("As of my last update January 2022..."), Mad-Libs blanks, phrasal templates with literal `[Your Name]` placeholders.

**Defense strength: zero.** Citation: Wikipedia "Signs of AI writing".

### Strict — corporate-speak, easy to ban for taste

These are real human patterns, but they're patterns the user explicitly wants out. The rule isn't "this proves AI wrote it" — it's "I find this voice cheap and want it gone." Defending these is possible but pointless inside a brand voice that has already rejected them.

Examples: leverage / utilize / harness / delve / foster / cultivate, filler adverbs (fundamentally, essentially, ultimately), filler openers ("In today's fast-paced world"), cliché closers ("What do you think?"), negative parallelism ("X isn't Y, it's Z").

**Defense strength: medium** (someone could defend "leverage" as 1980s management vocabulary). **Brand-voice strength: zero** — the user banned them.

### Aesthetic — overreach, defendable

These are patterns flagged because LLMs happen to use them, not because they signal AI. Famous human writers built careers on them. Detectors over-fire on these and produce false positives — see Stanford HAI / Liang et al. (2023) showing detectors are biased against non-native English writers, and the Adelphi University lawsuit over an AI false-positive accusation.

Examples: a single em dash (Emily Dickinson, Cormac McCarthy), the rule of three (Lincoln, Caesar, Churchill), passive voice (Watson & Crick, Joan Didion, all scientific writing), the word "robust" (a century of epidemiology and engineering papers), curly quotes (automatic in Word/Pages, New Yorker house style since 1925).

**Defense strength: high.** These are the rules Sergey's controversial post is built on.

## Non-negotiable rules

- Don't conflate tiers. A `[oaicite]` marker and a single em dash are not the same kind of evidence.
- When defending, name the writer and give the example. "Lincoln" is weaker than "Lincoln, Gettysburg Address, 1863: 'of the people, by the people, for the people'."
- Cite when available. Stanford HAI and the OpenAI classifier shutdown are the strongest external receipts.
- Don't defend a rule the user has personally banned (em dashes in his own voice, even though Dickinson used them). Brand voice overrides aesthetic defense.

## Example

> **Input:** "OriginalityAI flagged my post for using 'robust' — should I rewrite?"
>
> **Output:**
> Tier: aesthetic. The word "robust" has been used by epidemiologists, engineers, and statisticians for over a century — it has a precise meaning ("insensitive to assumption violations") that no synonym carries. OriginalityAI flags it because GPT-4 over-uses it, not because it signals AI. Defense strength: high.
>
> Recommendation: keep "robust" if you're describing a statistical model, a system architecture, or an immune response. Rewrite to "solid" only if you're using it as generic praise — that's the corporate-speak overuse the humanizer is actually targeting.
>
> Citation: Wikipedia "Signs of AI writing" lists "robust" under AI vocabulary; Stanford HAI shows detectors over-fire on technical English.

## Files

- `../references/rules-explainer.md` — full table of all 15 rules organized by tier, with famous-writer examples and citations

## Related skills

- `linkedin-humanizer` — applies the rules (this skill explains them)
- `linkedin-post-audit` — flags rules in a draft
- `sub-skills/detector-tester.md` (sibling) — runs OriginalityAI / GPTZero / Pangram against drafts
