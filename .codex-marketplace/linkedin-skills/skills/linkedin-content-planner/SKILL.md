---
name: linkedin-content-planner
description: Generate a 7-day LinkedIn content plan from a theme, audience, and pillars. Produces per-day post pillar, format, hook type, CTA, posting time, daily comment targets, and a weekly inbound-readiness check. Use when the user wants to plan a week or month of content, not draft a single post.
---

# LinkedIn Content Planner

Produce a 7-day LinkedIn plan built around the 3-pillar discipline (Authority 40-50%, Personal Narrative 30-40%, Community 20-30%). Optionally adds a Product/Offer pillar at 10-15%.

## When to use

- User asks "plan my week" or "what should I post this week"
- User wants to escape ad-hoc shipping and establish rhythm
- Before a launch week (user needs product-pillar alignment)

## Input

- **Theme** (optional): e.g., "AI agents shipping in production", "first 6 months of Co.Actor"
- **Audience description:** e.g., "B2B founders, AI ops leaders, marketing VPs"
- **Pillar mix** (optional): defaults to 40% Authority / 30% Narrative / 20% Community / 10% Product
- **Posting days** (optional): defaults to Tue/Wed/Thu/Fri (4 posts)
- **Voice samples** (optional): paths to past posts for voice calibration

## Output

A markdown plan with:

### 7-day calendar

| Day | Time | Pillar | Format | Hook formula | 1-line angle | CTA type | Goal |
|---|---|---|---|---|---|---|---|
| Mon | — | (commenting day) | — | — | — | — | — |
| Tue | 8:00 AM local | Authority | Text | F7 Odd-Precision Money | "What 3 months of agent ops costs" | Question close | Saves |
| Wed | 9:30 AM local | Narrative | Text | F4 Time-Anchor Confession | "Why I stopped publishing for 4 weeks" | Mirror question | Comments |
| Thu | 8:00 AM local | Community | Text | F14 Named Gratitude | "The 3 people who shaped our launch" | Tag + thanks | Reposts |
| Fri | 9:00 AM local | Narrative | Text | F11 Emotional Cold-Open | "The night our first deploy failed" | Soft close | Likes |
| Sat/Sun | — | (off) | — | — | — | — | — |

The Goal column spans saves / comments / reposts / likes across the four posts, satisfying the Goal mix check below.

### Daily comment targets

For each posting day:
- **3-5 creators to engage** (names or archetypes: "peer founders at 5-20k", "VCs with AI thesis", "BigCo CTOs")
- **Comment pattern** to apply (first-commenter, data-first, answer-their-question)
- **Target count:** 10-20 substantive comments per day

### Weekly inbound-readiness check

- [ ] At least 1 vulnerability post (Narrative)
- [ ] At least 1 receipt/data post (Authority)
- [ ] At least 1 soft offer or CTA-driving post
- [ ] Comment strategy includes 70% peers, 20% aspirational, 10% prospects
- [ ] No pillar >60% of the week's posts
- [ ] No duplicate formula used twice in the same week
- [ ] Goal mix spread: not every post chases the same reaction (see Goal mix below)

## Rules

- **3 pillars minimum, 5 maximum.** More than 5 dilutes signal.
- **3-5 posts per week.** 6+/week triggers cannibalization signal in 360Brew.
- **10-20 comments/day** on other creators. Comments drive more inbound than posts.
- **Tue/Wed/Thu** top for B2B. Avoid Fri after 2 PM, Sat/Sun (B2B 30-50% reach cut).
- **One format per pillar per week.** Don't stack 3 text posts for Authority — vary.
- **Product/Offer pillar max 1 post/week.** Overuse kills trust.

## Formula → pillar mapping

| Pillar | Preferred formulas |
|---|---|
| Authority | F7 Odd-Precision Money, F10 Contrarian Historical, F8 Paid-vs-Free, F5 Self-Proving Meta, F15 Explain-to-Kids |
| Narrative | F4 Time-Anchor Confession, F3 Year-over-Year Pivot, F9 Curiosity-Gap, F11 Emotional Cold-Open, F16 Status-Strip |
| Community | F6 Comment-Gate (use sparingly), F12 Permission Slip, F14 Named Gratitude, poll posts, spotlight mentions |
| Product/Offer | F2 R.I.P. Obituary (when pivoting category), F1 Anaphora (when framing product as fix), F13 Bait-and-Switch (upgrade announcements) |

## Goal mix (balance the week, not just the pillars)

Every formula earns a primary reaction: comments, reposts, likes, or saves (see `../../references/hook-formulas.md` "Engagement-goal split"). A week that is all comment-bait or all repost-bait reads as engineered and flattens reach. Spread the goals across the week:

| Goal | Formulas | Weekly target |
|---|---|---|
| Comments | F4, F10, F12, F9 | at least 1 |
| Reposts | F14, F2, F8 | at least 1 |
| Likes | F11, F13, F16 | at least 1 |
| Saves | F15, F7, F8 | at least 1 |

## Steps

1. Gather inputs. Ask user for theme, audience, pillar preferences if not provided.
2. Validate pillar mix sums to 100%; warn if any pillar >60%.
3. For each posting day, pick:
   - Pillar (rotate to match mix)
   - Formula from that pillar's bank (don't repeat within 7 days)
   - Format (alternating text / carousel / poll per pillar rules)
   - Specific angle (user provides or skill generates)
   - Posting time (audience-timezone aware)
4. For each posting day, add 3-5 comment targets with suggested pattern.
5. Run inbound-readiness check; flag anything missing.
6. Return as markdown + optional JSON for Notion/Airtable import.

## Example

See `references/example-plan-week.md` for a filled-in 7-day plan.

## Files

- `SKILL.md` — this file
- `references/example-plan-week.md` — worked example
- `references/pillars-framework.md` — the 3-pillar discipline explained

## Related skills

- `linkedin-post-writer` — generate each day's draft from the plan
- `linkedin-comment-drafter` — execute the daily comment targets
- `linkedin-thread-monitor` — track inbound from the comment strategy
- `linkedin-engager-analytics` — segment audience on each post
