# 2026 LinkedIn Posting Heuristics

Based on 360Brew paper (arXiv 2501.16450), AuthoredUp 2026 reach data, Trust Insights Q1 2026 guide, and Social Media Today reporting on Gyanda Sachdeva's anti-pod measures.

## Timing

| Audience | Best window (local) |
|---|---|
| US B2B / founders | Tue 8:00 AM ET, Wed 10:00 AM ET |
| EU decision-makers | Tue/Wed 7:00-8:30 AM CET |
| Global mixed | Tue/Wed/Thu 7:30-9:00 AM, audience timezone |

Avoid: Mon before 9 AM, Fri after 2 PM, Sat/Sun (30-50% reach cut for B2B).

## Format reach multipliers (relative to single image)

| Format | Multiplier |
|---|---|
| Document carousel (PDF) | 1.7-2.3x |
| Native video (<90s, captioned, vertical 9:16) | 1.4-1.8x |
| Text-only | 1.0-1.3x |
| Poll | 1.1x |
| Single image | 1.0x (baseline) |
| External link in body | 0.4-0.6x |

## Length

- Sweet spot: **900-1,300 chars** (~150-220 words)
- Hook cutoff: **first 210 chars** (mobile "… see more" line)
- Long-form (1,500-1,900) works only with line breaks every 1-2 sentences and narrative payoff
- Avoid <400 chars unless you're an established voice with punchy observations

## Hashtags

- **0 hashtags** performs equal to or better than 5+ in 2026 (360Brew uses semantic embeddings, not tag matching)
- **1-3 niche hashtags** (<50k posts) give marginal lift (~5%)
- **5+ hashtags** correlate with spammy-account patterns (negative signal)
- Placement: end of post, never mid-sentence

## Link placement

- **Link in first comment:** ~2.1x impressions vs in-body link
- **In-body:** suppressed 40-60%
- **Workaround phrasing:** "Source below ↓", "Dropped the piece in comments"

## Signal weights (reported; not officially confirmed)

- Save = **5x a like**, 2x a comment
- In-depth comment (paragraph-length) > one-word reaction by 4x
- Comment-to-comment threading (user↔user replies) = strong quality signal
- Dwell time sweet spot: **31-60 seconds**
- "See More" expand + fast abandon (<3s) = clickbait penalty
- First 1-2 sentences scored for topic relevance before user scrolls

## First 60 minutes

- 60-90 min "Momentum Window" determines 80% of total reach
- Author reply to every comment within 90 min = required to hit the ceiling
- If 3+ substantive comments arrive in first 30 min, post gets second testing boost

## Penalties

- Comment pods: **97% detection accuracy** (third-party claim, unconfirmed). Penalty: shadowban 3-14 days, reach cut 60-90%.
- TOS change: "We may limit how many comments a member can make in a time period."
- Recycled reply templates on own post: lexical-similarity detection downranks.
- Over-posting: 2+ posts/day triggers cannibalization signal (360Brew deprioritizes accounts posting 2+/day).

## Native articles

- Lift is real but modest: ~1.2-1.4x vs regular text post
- Long-tail SEO via Google indexing (bonus)
- Use for evergreen/reference; not for timely takes

## 2026 AuthoredUp format benchmarks (absolute engagement rates)

| Format | Engagement rate / reach |
|---|---|
| Multi-image (3-4 personal photos) | **6.60%** engagement rate (highest of all formats) |
| Carousel (doc post, 6-9 slides, <12 words/slide) | ~6x engagement, ~4x reach vs text-only |
| Poll | +206% reach vs average post |
| Single image | 0.7x (now underperforms text-only by ~30%) |
| Native video (30-90s, captioned) | reach -35% YoY in 2026; still viable with strong hook |

## Native video rules

- Length: **30-90 seconds**
- Captions mandatory (85% of users watch without sound)
- **Native upload only** — YouTube links kill reach
- Hook visually in first 3 seconds
- Vertical 9:16, not landscape

## Hook cutoff (device-specific)

- Desktop: ~210 chars before "…see more"
- **Mobile: ~140 chars before "…see more"**
- Write for the 140-char mobile line; the desktop window is a bonus.

## Close mechanics

- Specific closing question (e.g., "What's your experience with X?") boosts engagement **20-40%** vs generic "Thoughts?"
- Name the topic inside the CTA — generic CTAs don't trigger replies.

## Save ratio absolute case

- 200 saves ≈ **4x the reach** of 1,000 likes
- Checklists, frameworks, and templates are save-bait — optimize for save, not like.

## Engagement benchmarks by follower count

| Follower count | Expected engagement rate |
|---|---|
| 1K-5K | 4-8% |
| 5K-10K | 3-5% |
| 10K-50K | 2-4% |
| 50K+ | 1-3% |

Use to calibrate whether a post underperformed or is within band before blaming the algorithm.

## Comment-weight math (reach multipliers)

- Comments weigh **~3x more than likes** for reach
- Posts with back-and-forth conversation: **3x reach** of posts with passive engagement
- Posts where the author replies to commenters: **2x+ distribution**
- Author-replied comments count as a **fresh ranker signal each time**

## Pod / pattern detection (avoid)

Triggers for suppression:
- 15+ comments landing within a 90-second window
- Same accounts engaging at the same clock minute daily (e.g., 9:01 AM)
- Identical like/comment pattern across every post

Observed real consequence: one creator dropped from 8,500 to 340 impressions overnight after pod detection.

**Recovery times:**
- From pod detection: **6-8 weeks**
- Already-credible account cold start: ~1 week
- New account cold start: 30-60 days

## External-link penalty (expanded)

- External links in post body: **~60% reach reduction** (move to first comment)
- Engagement-bait CTAs ("Agree? Comment below!") now **actively suppressed**, not just ignored
- **Viewer tolerance score:** if users scroll past your posts without dwelling, distribution progressively collapses even for followers

## Edit-safety window

- Edits within first **3 hours** trigger a re-evaluation
- Structural restructuring (>20% of text changed) **resets distribution entirely**
- Typo fixes safe after the 90-min momentum window

## Post-publish engagement windows

| Phase | Window | Action |
|---|---|---|
| Warm-up | 15 min **BEFORE** publishing | Leave 3-5 substantive comments on others' posts |
| Critical | First 30 min AFTER publishing | Reply to every comment within minutes |
| Seeding | 15-30 min after posting | Leave 3-5 bonus comments on your own post to create thread depth |
| Visibility bump | Reply within 1st hour | +35% visibility lift |

## Pre-publish checklist

- [ ] Hook fits in first 210 chars
- [ ] No em dashes (`—`), en dashes (`–`), double dashes (`--`)
- [ ] No AI vocabulary blacklist (leverage, fundamentally, delve, etc.)
- [ ] At least 1 specific number per 100 words
- [ ] At least 1 named entity (person, company, product)
- [ ] At least 1 first-person concrete detail (what you saw, did, said)
- [ ] No external links in body
- [ ] 0-2 hashtags at end
- [ ] Length 900-1,300 for medium, 1,500-1,900 for long
- [ ] Line breaks between ideas, not every sentence
- [ ] One moment of real vulnerability or stakes
- [ ] Close is a question OR a clean landing (not "what do you think?")
