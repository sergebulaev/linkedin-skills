# LinkedIn Detector Tester

Pipes any text through 5+ AI detectors at once and prints how badly they disagree. The point is not to find the "right" score. The point is to show there is no right score.

## Before you run it: your draft leaves your machine

This is the one skill in the bundle that sends your text to someone else. Every detector
here is a hosted API, so running it uploads the draft, in full, to whichever services you
have keys for: GPTZero, Originality.ai, ZeroGPT, Sapling, Copyleaks, Hive, QuillBot,
Writer and Scribbr. Nothing else in this bundle does that. Drafting, scrubbing, auditing
and profile-building all happen locally, and publishing goes only to Publora.

What that means in practice:

- **An unpublished post is not private once you test it.** Treat the text as disclosed to
  every provider whose key is set, under their terms and retention policy, not ours.
- **Do not run it on anything confidential**: unannounced launches, client names, numbers
  under embargo, anything covered by an NDA.
- **Only the detectors you have keys for are called.** No key, no request to that service.
  Running with no keys at all makes no network calls.
- It is worth asking whether you need it. The verdict this sub-skill exists to deliver is
  that the scores disagree and none of them mean much, which is a point you can take on
  trust rather than paying for with your draft.

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
cd /home/sbulaev/p/linkedin-skills/skills/linkedin-humanizer
python3 scripts/test_detectors.py --text "$(cat draft.txt)"
```

Or pipe in:

```bash
cat draft.txt | python3 scripts/test_detectors.py --stdin
```

Most detectors gate their API behind paid plans. The script supports three modes:

1. **API mode** — copy `../scripts/detectors.env.example` to `.env` and fill the keys you have (`GPTZERO_API_KEY`, `ORIGINALITY_API_KEY`, `ZEROGPT_API_KEY`, `SAPLING_API_KEY`, `COPYLEAKS_API_KEY` + `COPYLEAKS_EMAIL`). Detectors with valid keys run automatically; missing-key detectors are dropped from the report.
2. **Manual paste mode** (`--manual`) — opens each detector's web UI, prompts the user to paste the score back. Slower but free, and captures detectors with no API.
3. **Demo mode** (`--demo`) — offline. Returns deterministic canned scores derived from a hash of the input. No API calls, no keys needed. Use to smoke-test the workflow or to demonstrate the divergence pattern without spending API credit.

Install dependencies first:

```bash
pip install -r ../../../requirements-lock.txt
```

## Files

- `../references/detector-list.md` — supported detectors, API endpoints, known accuracy issues, citations
- `../scripts/test_detectors.py` — runs the parallel test, computes spread, prints verdict
- Python deps (`requests`, `python-dotenv`) come from the bundle's own
  `../../../requirements.txt`, pinned in `../../../requirements-lock.txt`. The script
  has no separate manifest: one that has to be kept in sync with the root is one that
  drifts, and this one already had.
- `../scripts/detectors.env.example` — template for the 5 detector API keys (copy to `.env`)

## Related skills

- `linkedin-humanizer` — rewrites text after a high score (or before, defensively)
- `post-audit.md` (sibling) — pre-publish check that catches AI tells without relying on detectors

## What this skill is not

It is not a detector. It does not claim a piece of text is or is not AI-written. It only documents how much the existing detectors disagree, so that a single score can never again be used as a trump card.
