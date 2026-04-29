---
name: linkedin-engagement-monitor
description: Monitor LinkedIn engagement on two surfaces. (1) Author replies to your comments (the highest-value inbound signal, with the 6-24h Kevin Payne window). (2) Likers and commenters on any post, grouped by ICP fit, seniority, company, peer / aspirational / prospect tier. Drafts timely follow-ups for warm threads and produces ICP-segmented engager reports for outbound. Powered by Apify (no LinkedIn login required). Keywords thread monitoring, author reply, inbound tracking, comment follow-up, engagement compound, likers analysis, post engagers, ICP segmentation, audience analytics, who engaged.
---

# LinkedIn Engagement Monitor

Two read-side workflows, one skill.

1. **Thread monitoring.** Track which of your comments earned author replies, draft timely follow-ups, flag the 6-24h Kevin Payne window where thread momentum is highest.
2. **Engager analytics.** Pull every liker and commenter on any post, group them by ICP fit, surface peer / aspirational / prospect tiers, and feed the result into your DM or outreach queue.

Both workflows depend on `APIFY_TOKEN`. Without it, fall back to user-paste.

## When to use

- Daily: "What threads need follow-up today?"
- After posting a batch of comments: "Check back in 6 hours"
- When an author replied personally: "Draft the response"
- After publishing a post: "Who actually engaged? Are they ICP?"
- Before a campaign: "Pull the last 5 viral posts in my niche, group their commenters by company size"

## Input

- Mode 1 (thread monitoring): your LinkedIn handle (last path segment of profile URL).
- Mode 2 (engager analytics): one or more LinkedIn post URLs.
- Optional for both: ICP definition (target titles, company size, industry).

## Mode 1. Thread monitoring

### Output

#### Daily report

| Posted | Author | Post | Comment | Reply? | Stage | Action |
|---|---|---|---|---|---|---|
| 18h ago | Kevin Payne | LawVu | "moat moved to taste" | Kevin replied 14h ago | Warm (6-24h window) | Reply now |
| 22h ago | Dharmesh Shah | HubSpot | "integration depth moat" | No | Cold | Skip |
| 3h ago | Felix T. | Rezolve | "twin economies" | No | Watch | Check in 3h |

#### For each warm thread
- Thread preview (last 3 turns)
- Suggested response (drafted via `linkedin-reply-handler`)
- Reaction target (the specific reply URN, not the post)
- Priority (high / medium / low)

#### Weekly roll-up
- Total comments posted
- Author-reply rate (target 15%+)
- Conversion to DM (when thread closes warm)

### Steps (Mode 1)

1. **Fetch user's recent comments.** If `APIFY_TOKEN` is set, call `lib.ApifyClient.fetch_user_recent_comments(username=<your-handle>, result_limit=30)`. Each item already includes the parent post body, post URL, post author, and reaction stats. If `APIFY_TOKEN` is not set, ask the user to list (or paste) the URLs of comments they've posted in the last 72h.
2. **For each comment posted in last 72h:** check the parent post's comment tree (use `fetch_post_comments(post_id=..., scrape_replies=True)`) for:
   - Replies to the user's comment
   - Whether the author posted any of those replies
   - Timestamps (time since user's comment, time since latest reply)
3. **Classify stage:**
   - Hot (<6h): author just replied. Respond within 90 min for max thread momentum
   - Warm (6-24h): the Kevin Payne window. Author replies most happen here
   - Cool (24-72h): still respondable but lower velocity
   - Dormant (>72h): don't reply in thread. Consider DM
4. **Draft responses** for warm threads using `linkedin-reply-handler`.
5. **Flag suspicious patterns:**
   - Author replied but also deleted someone else's comment (author is actively moderating, tread carefully)
   - Commenter is in thread self-promoting (your reply shouldn't engage them)
6. **DM routing:** if thread is dormant but the author engaged meaningfully, draft a DM that references the thread specifically.

### Kevin Payne window

Named after the real 2026-04 data point: Kevin Payne (LawVu CEO) replied to Serge's comment 22h after the original post. This is the sweet spot.

- 0-6h: 70% of author replies happen here if they're going to happen
- 6-24h: ~25% of author replies, but these are higher-quality (author took time to think)
- \>24h: thread rarely produces new author engagement

Follow-up timing:
- If author replied in 0-6h window: respond within 90 minutes
- If author replied in 6-24h window: respond within 2 hours (they're still checking)
- If author replied >24h: respond within 4 hours before thread goes cold

## Mode 2. Engager analytics

### Output

#### Engager roster

| # | Type | Name | Title | Company | Profile | ICP tier |
|---|---|---|---|---|---|---|
| 1 | commenter | Jordan Boynton | Director | Cerberus Cosmetics | linkedin.com/in/... | Prospect |
| 2 | commenter | Adaita Mishra | Senior PM | Atlassian | linkedin.com/in/... | Aspirational |
| 3 | liker | Lara Acosta | Founder | Lara LLC | linkedin.com/in/... | Peer |

#### Tier breakdown

| Tier | Definition | Count | % of total |
|---|---|---|---|
| Peer | Founder / operator at company in same niche, 5-50 employees | 12 | 24% |
| Aspirational | Senior leader at 50+ company in adjacent niche | 9 | 18% |
| Prospect | Director / C-suite at company matching ICP | 18 | 36% |
| Other | Doesn't fit any tier | 11 | 22% |

#### Action lists
- **Follow back** (peers worth reciprocal engagement): top 5 by activity
- **Comment-drop targets** (aspirational creators with their own posts): top 5
- **DM-able prospects** (with the rationale): top 5 with one-line opener seed

### Steps (Mode 2)

1. **Fetch engagers.** Call `lib.ApifyClient.fetch_post_engagers(post_url=<url>, max_items=100)`. Returns a list of dicts with `type` ("commenters" | "likers"), `name`, `subtitle` (job title + company), `url_profile`, `content` (comment text if commenter), `datetime`. Cost is roughly $0.005 per engager-record.
2. **Parse subtitle into structured fields.** The `subtitle` typically reads "Director at Cerberus Cosmetics" or "Founder & CEO at LawVu". Extract: title, company, seniority bucket (IC / Manager / Director / VP / C-suite / Founder).
3. **Score ICP fit.** Use the user's supplied ICP rules:
   - Title match (regex or keyword list)
   - Company size proxy (look up via the user's CRM if integrated, else mark Unknown)
   - Industry match (parse company name + subtitle keywords)
4. **Assign tier.**
   - Peer: founder / operator at similar-stage company in same niche
   - Aspirational: senior leader (Director+) at larger company in adjacent niche
   - Prospect: title in ICP target list AND company in ICP target list
   - Other: no match
5. **Produce action lists.**
   - Follow back: peers with active posting (heuristic: appears as author in `fetch_user_recent_comments` of any team member)
   - Comment-drop targets: aspirational tier
   - DM-able: prospect tier, with a one-line DM opener referencing the specific post they engaged with ("Saw you reacted to <post angle>. Curious. Are you currently <ICP problem>?")
6. **Optional cross-post analysis.** If the user supplied multiple post URLs, deduplicate engagers and flag people who engaged with 2+ posts (highest-intent signal).

## Inbound-quality signals (apply to both modes)

High-quality engager = worth the follow-up:
- Founder / operator title in profile
- Company in user's ICP
- Active posting history (not just reactions)
- Mutual 2nd-degree connections >10
- Prior thoughtful comments on user's posts

Low-quality = skip:
- Generic praise with no specifics
- Template language ("I'd love to hop on a quick call")
- Profile is sales / agency with no operator history
- Same comment across many creators' posts

## Hard rules

- Never reply to a reply later than 72h after the thread's last turn. Switch to DM.
- Never chain 3+ replies under one comment (thread spam).
- If the author deleted their reply, do not reply. They reconsidered.
- Don't DM a warm thread before first replying publicly (skips a step).
- Don't DM a prospect on the same day they engaged with your post. Wait 24-72h to avoid the "thirsty" pattern.
- Don't run engager analytics on posts you didn't write or aren't tracking with permission. The data is technically public but high-volume scraping of someone else's audience reads as creepy.

## Examples

### Mode 1. Thread monitoring

> Input: monitor sbulaev profile, last 24h

> Output:
> - 1 warm thread: Kevin Payne replied 14h ago on LawVu post. Current stage: Warm (8-24h). Suggested response ready. Action: post within 2 hours.
> - 8 cold threads (no author engagement). Skip.
> - 3 watching threads (<6h old, author may still reply). Check again in 3-6h.

### Mode 2. Engager analytics

> Input: analyze engagers on https://www.linkedin.com/posts/satyanadella_..., max 100

> Output:
> - 50 commenters fetched ($0.25)
> - Tier split: 6 Peer / 14 Aspirational / 18 Prospect / 12 Other
> - 3 cross-post engagers detected (also engaged with my post 2 weeks ago)
> - Top 5 DM-able prospects with one-line openers attached

## Cost accounting

| Action | Apify call | Cost (free tier) |
|---|---|---|
| Daily thread sweep (1 user, ~30 comments) | `fetch_user_recent_comments` once | $0.005 |
| Per-warm-thread context | `fetch_post_comments(scrape_replies=True)` | $0.005 each |
| Engager analytics on one post (50 engagers) | `fetch_post_engagers(max_items=50)` | $0.25 |
| Engager analytics on one post (200 engagers) | `fetch_post_engagers(max_items=200)` | $1.00 |

A typical creator running this skill 5 days/week with 1 engager-analytics run/week stays well under the $5 free monthly credit.

## Files

- `SKILL.md` — this file
- `references/thread-timing.md` — the timing matrix with examples (Mode 1)

## Related skills

- `linkedin-reply-handler` — drafts the actual follow-up message for warm threads
- `linkedin-comment-drafter` — drafts the initial comment that starts threads
