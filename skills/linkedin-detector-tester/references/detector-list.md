# Supported AI Detectors

Last updated: 2026-04-25

Five primary detectors plus optional extras. Each entry covers: API endpoint, auth, known accuracy issues, and the citation that documents the issue.

---

## 1. GPTZero

- **Web**: https://gptzero.me
- **API docs**: https://api.gptzero.me/v2/predict/text
- **Auth**: `x-api-key` header. Free tier: 10k words/month. Paid from $9.99/mo.
- **Returns**: `documents[0].class_probabilities.ai` (0.0-1.0) plus per-sentence breakdown.

**Known issues:**
- Stanford study (Liang et al. 2023) included GPTZero in the cohort that flagged **61.3% of TOEFL essays** from non-native English writers as AI. ESL bias is documented and reproducible.
- Inflates scores on technical / dense prose regardless of authorship.
- Will not run on text under 250 characters; gives unstable scores under 100 words.

**Citation**: Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). "GPT detectors are biased against non-native English writers." *Patterns*, 4(7). https://doi.org/10.1016/j.patter.2023.100779

---

## 2. Originality.ai

- **Web**: https://originality.ai
- **API docs**: https://docs.originality.ai/
- **Auth**: `X-OAI-API-KEY` header. No free tier — $0.01 per 100 words minimum.
- **Returns**: `score.ai` (0.0-1.0), `score.original` (0.0-1.0).

**Known issues:**
- Marketed as "99% accurate" but multiple independent tests put real-world accuracy in the 60-80% range.
- Aggressively flags any text that has been edited by Grammarly or similar tools, since editing patterns mimic LLM patterns.
- Sergey's team meeting test (2026): scored a hand-written article **100% AI** while GPTZero scored the same article 82% and ZeroGPT scored 50%. 50-point spread on identical text.

**Citation**: Internal CCC team test, March 2026 meeting transcript (`projects/coactor/transcripts/`); also referenced in Sergey Bulaev's April 2026 LinkedIn post on detector unreliability.

---

## 3. ZeroGPT

- **Web**: https://www.zerogpt.com
- **API docs**: https://api.zerogpt.com/api/detect/detectText
- **Auth**: `ApiKey` header. Free tier: 5 requests/min. Paid plans available.
- **Returns**: `data.fakePercentage` (0-100 integer), `data.isHuman` boolean.

**Known issues:**
- Famously unstable — the same input pasted twice 30 seconds apart can return scores 20+ points apart.
- Flags US Constitution, Bible verses, and Declaration of Independence at 90%+ AI when pasted as plain text.
- Susceptible to trivial paraphrasing — adding two typos drops a 95% score to 30%.

**Citation**: Multiple replicated demos on Twitter/X 2023-2024; Vanderbilt University communication on disabling Turnitin (Aug 2023) cited similar instability across the detector category. https://www.vanderbilt.edu/brightspace/2023/08/16/guidance-on-ai-detection-and-why-were-disabling-turnitins-ai-detector/

---

## 4. Sapling

- **Web**: https://sapling.ai/ai-content-detector
- **API docs**: https://sapling.ai/docs/api/aidetect
- **Auth**: `key` field in JSON body. Free tier: 50 requests/day.
- **Returns**: `score` (0.0-1.0), per-sentence `sentence_scores`.

**Known issues:**
- Tends to score lower than GPTZero/Originality on the same text — useful as a contrarian signal in the parallel test.
- Worse on creative writing than on technical prose.
- Does not handle markdown — strip formatting before sending.

**Citation**: Sapling's own published benchmarks (https://sapling.ai/ai-content-detector/benchmark) acknowledge ~3-5% false positive rate even in their best-case dataset.

---

## 5. Copyleaks

- **Web**: https://copyleaks.com/ai-content-detector
- **API docs**: https://api.copyleaks.com/documentation/v3/writer-detector/submit
- **Auth**: 2-step. POST to `/v3/account/login` with email + key, get bearer token, then POST to `/v2/writer-detector/{scanId}/check`.
- **Returns**: `summary.ai` (0-100), per-paragraph breakdown.

**Known issues:**
- Adelphi University used Copyleaks-style detector output as the sole evidence in the case that became *Newby v. Adelphi University* (Oct 2025). Federal court ordered the violation expunged.
- Heavily penalizes formal academic writing regardless of authorship.
- Unstable across re-submissions of the same text.

**Citation**: *Newby v. Adelphi University*, U.S. District Court (E.D.N.Y.), October 2025. Coverage: Inside Higher Ed, "Court Orders University to Drop AI-Cheating Charge" (Oct 2025).

---

## Optional / extended detectors

These can be added via `--extra` flag. None have free APIs.

- **Turnitin AI Writing** — disabled by Vanderbilt, Cambridge, others. No public API; institutional only.
- **Winston AI** — https://gowinston.ai. Paid only.
- **Crossplag AI** — https://crossplag.com. Paid only.
- **Writer.com AI Content Detector** — free web UI, no API. Use `--manual` mode.
- **Scribbr AI Detector** — free web UI, no API. Use `--manual` mode.

---

## Why the spread matters

OpenAI shut down its own AI Text Classifier in July 2023 with this public statement: "low rate of accuracy" — internally measured at 26%. If the company that ships the model cannot reliably detect its own output, no third-party detector built on weaker signals can be trusted as ground truth.

Reference: OpenAI blog, "New AI classifier for indicating AI-written text" (Jan 31, 2023), updated July 2023 with discontinuation notice.

---

## Quick stats to drop in a reply

- **61.3%** — TOEFL essays by ESL writers misclassified as AI by 7 detectors (Stanford 2023)
- **5.1%** — same detectors' false positive rate on US 8th-grade essays (Stanford 2023)
- **26%** — OpenAI's own classifier accuracy before shutdown (July 2023)
- **50 points** — spread observed on a single article in CCC team testing (2026)
- **0** — number of US courts that have upheld a "detector said so" finding without corroborating evidence as of April 2026
