# Emoji Patterns — AI vs. Human

Pattern data from Naïlé Titah / MagicPost LinkedIn analysis (Feb 2026, viral post with 220 engagement).

Source frequencies measured across a corpus of AI-generated vs. human-authored LinkedIn posts. The percentage column shows how often each emoji appears in AI-generated content.

## AI-correlated emojis (the "tells")

| Emoji | Name | AI Frequency | Why it's a tell | Human-pattern alternative |
|-------|------|--------------|-----------------|---------------------------|
| 💡 | lightbulb | 2.57% | ChatGPT signature for "insight" / "tip" — most diagnostic single emoji | 🪛 (screwdriver) for fix-it posts, 📍 (pin) for highlights, or remove |
| 🚀 | rocket | 3.28% | Highest-frequency AI emoji. Signals "launch" / "growth" in template fashion | 📦 (box) for shipping, 🛫 (takeoff) for travel, or remove |
| ✨ | sparkles | 3.11% | "Magic AI" / "transformation" cliché. Almost never appears in human ops content | Remove. No clean substitute |
| ♻️ | recycling | 2.93% | Used to flag re-shares and "lessons learned" loops. AI overuses for filler | 🔁 (repeat) only if literally about repetition, or remove |
| 🎯 | target | 2.07% | "Goals" / "objectives" cliché | 📌 (pushpin) for specific items, or remove |
| 📈 | chart_increasing | 1.89% | "Growth" / "metrics" template signal | Use a real number in plain text instead |
| 🔑 | key | 1.74% | "Key takeaway" / "key insight" template | Skip the emoji, write the takeaway in plain prose |
| 🎯 | dart | 1.68% | Same family as target above — both flag templated structure | Same as target |
| 💪 | muscle | 1.45% | "Strength" / "resilience" platitude | Remove or replace with concrete detail |
| 🔥 | fire | 1.31% | Borderline — used in human content too, but flagged when clustered with others | Keep if standalone, swap to 🌶️ (chili) or 🥵 (hot face) for variety |

## Cluster rules

- 1 AI-pattern emoji in isolation: usually fine
- 2 in one post: borderline — flag in `--strict` mode
- 3+ in one post: AI-likely — flag in all modes
- Same emoji 2+ times: repetition tell — flag in all modes

## Position rules

AI-generated posts tend to put emojis at:
- End of opening hook line (lightbulb, rocket, sparkles)
- Start of every bullet in a list (target, key, fire)
- End of CTA line (rocket, fire, muscle)

If the draft has emojis at all three positions, treat as AI-likely regardless of which emojis they are.

## Human-pattern emojis (sub-1% AI correlation)

These appear at much lower frequency in AI-generated content. Not "human-proof" — just less of a tell:

| Emoji | Name | Notes |
|-------|------|-------|
| ☕ | coffee | Concrete, mundane — AI rarely uses |
| 🍕 | pizza | Specific food — AI rarely uses |
| 📦 | package | Shipping / ops — concrete |
| 🪛 | screwdriver | Fix-it posts — newer emoji, AI training lags |
| 🌶️ | chili | "Spicy take" replacement for fire |
| 📍 | round_pushpin | Specific location / item highlight |
| 🛫 | airplane_departure | Travel / launch — more specific than rocket |
| 🥵 | hot_face | Reaction emoji — less templated than fire |
| 🪟 | window | Newer emoji, AI training lags |
| 🧃 | beverage_box | Newer emoji, AI training lags |

## What this data does NOT prove

- It doesn't prove these emojis are "wrong" — humans use 💡 and 🚀 too
- It proves they appear 2-3x more often in AI-generated content than baseline
- A single AI-pattern emoji in a post is not a verdict — the cluster + repetition pattern is the tell
- New emojis released after model training cutoffs are mechanically less likely to appear in AI output, which is why the human-pattern list skews toward newer Unicode additions

## Update cadence

Frequencies should be re-measured quarterly as AI training data shifts. Last update: Feb 2026 (Naïlé Titah / MagicPost).
