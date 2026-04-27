---
name: linkedin-detector-tester
description: Run text through GPTZero, Originality.ai, ZeroGPT, Sapling, Copyleaks in parallel. Show divergence between detectors to expose unreliability. Keywords: AI detector, GPTZero, Originality.ai, ZeroGPT, Copyleaks, false positive, ESL bias, AI detection accuracy.
---

# LinkedIn Detector Tester

Pipes any text through 5+ AI detectors at once and prints how badly they disagree. The point is not to find the "right" score. The point is to show there is no right score.

## Why this exists

AI detectors get treated like medical tests. They are not. They are vibe checks with a percentage sign.

The receipts:

- **Stanford 2023** (Liang et al., Patterns / Cell Press): 7 AI detectors flagged **61.3% of TOEFL essays from non-native English speakers** as AI-generated. Same detectors flagged 5.1% of US-born 8th graders. The bias is against ESL writers, not against AI.
- **OpenAI shut down its own AI Text Classifier in July 2023** because it hit only **26% accuracy** on AI-written text. The company that builds the AI could not reliably detect the AI.
- **Vanderbilt University disabled Turnitin's AI detection** citing false-positive risk to students. Other R1 schools followed.
- **Newby v. Adelphi University (October 2025)**: a federal court ordered the university to expunge an AI-cheating violation from a student's record after the only "evidence" was a detector score.
- **Sergey's team test**: same article, three detectors, scores **82% / 100% / 50%**. That is a 50-point spread on identical text.

If accusations are coming, this skill produces the screenshot.

## When to use

- Someone accuses a post, essay, or proposal of being AI-written based on a single detector score
- Before defending a writer publicly, get the spread on record
- As a follow-up to Sergey's controversial detector post — paste any flagged text, run it, screenshot the divergence
- Internal QA on Co.Actor drafts before publishing to high-stakes audiences

## Input

Any text. 200+ words gives the most stable spread; under 100 words and detectors get even more random.

Optional: a label (e.g. "ESL student essay", "GPT-4 output", "1995 Carl Sagan column") for the output header.

## Output

```
Text: "<first 60 chars>..."
Length: 412 words

Detector scores (% AI probability):
  GPTZero         82
  Originality.ai  100
  ZeroGPT         50
  Sapling         34
  Copyleaks       91

Min: 34   Max: 100   Spread: 66

Verdict: USELESS — detectors disagree by more than 50 points.
Translation: nobody actually knows. The accusation is a coin flip.
```

## The three verdicts

| Spread (max - min) | Verdict | What it means |
|---|---|---|
| ≤ 15 points | **CONSENSUS** | Detectors agree. Still not proof, but at least they're not contradicting each other. |
| 16-30 points | **MIXED** | Some signal, but enough disagreement that no single score is defensible. |
| 31-50 points | **DIVERGENT** | The detectors are flipping a coin. |
| > 50 points | **USELESS** | The spread is bigger than half the scale. Whatever you decide, the opposite detector also "proves" it. |

## How to run

```bash
cd /home/sbulaev/p/linkedin-skills/skills/linkedin-detector-tester
python3 scripts/test_detectors.py --text "$(cat draft.txt)"
```

Or pipe in:

```bash
cat draft.txt | python3 scripts/test_detectors.py --stdin
```

Most detectors gate their API behind paid plans. The script supports two modes:

1. **API mode** — set keys in `.env` (`GPTZERO_API_KEY`, `ORIGINALITY_API_KEY`, `ZEROGPT_API_KEY`, `SAPLING_API_KEY`, `COPYLEAKS_API_KEY`, `COPYLEAKS_EMAIL`). Detectors with valid keys run automatically.
2. **Manual paste mode** — `--manual` flag opens each detector's web UI, prompts the user to paste the score back. Slower but free, and captures detectors with no API.

## Files

- `SKILL.md` — this file
- `references/detector-list.md` — supported detectors, API endpoints, known accuracy issues, citations
- `scripts/test_detectors.py` — runs the parallel test, computes spread, prints verdict

## Related skills

- `linkedin-humanizer` — rewrites text after a high score (or before, defensively)
- `linkedin-post-audit` — pre-publish check that catches AI tells without relying on detectors

## What this skill is not

It is not a detector. It does not claim a piece of text is or is not AI-written. It only documents how much the existing detectors disagree, so that a single score can never again be used as a trump card.
