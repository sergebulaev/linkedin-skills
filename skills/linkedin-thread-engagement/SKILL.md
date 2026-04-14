---
name: linkedin-thread-engagement
description: Monitor LinkedIn threads where the user commented for author replies and inbound signals. Use when the user wants to track which of their comments earned personal replies from post authors (the highest-value engagement signal). Flags the 6-24h "Kevin Payne window" where author replies are most likely, drafts follow-up responses, and optionally routes to DM. Keywords: thread monitoring, author reply, inbound tracking, comment follow-up, engagement compound.
---

# LinkedIn Thread Engagement

The engagement compounding layer. Tracks which of the user's comments earned author replies, drafts timely follow-ups, and flags the 6-24 hour window where thread momentum is highest.

## When to use

- Daily: "What threads need follow-up today?"
- After posting a batch of comments: "Check back in 6 hours"
- When an author replied personally (e.g., Kevin Payne → Serge): "Draft the response"

## Input

- User's LinkedIn profile URL (to pull their recent comments)
- Optional: specific post URL to monitor

## Output

### Daily report

| Posted | Author | Post | Comment | Reply? | Stage | Action |
|---|---|---|---|---|---|---|
| 18h ago | Kevin Payne | LawVu | "moat moved to taste" | ✅ Kevin replied 14h ago | Warm (6-24h window) | **Reply now** |
| 22h ago | Dharmesh Shah | HubSpot | "integration depth moat" | No | Cold | Skip |
| 3h ago | Felix T. | Rezolve | "twin economies" | No | Watch | Check in 3h |

### For each warm thread
- Thread preview (last 3 turns)
- Suggested response (drafted via `linkedin-reply-handler`)
- Reaction target (the specific reply URN, not the post)
- Priority (high / medium / low)

### Weekly roll-up
- Total comments posted
- Author-reply rate (target: 15%+)
- Conversion to DM (when thread closes warm)

## Steps

1. **Fetch user's recent comments** via HarvestAPI `/linkedin/profile-comments`.
2. **For each comment posted in last 72h:** fetch the parent post's comment tree and look for:
   - Replies to the user's comment
   - Whether the author posted any of those replies
   - Timestamps (time since user's comment, time since latest reply)
3. **Classify stage:**
   - **Hot (<6h):** author just replied — respond within 90 min for max thread momentum
   - **Warm (6-24h):** the Kevin Payne window — author replies most happen here
   - **Cool (24-72h):** still respondable but lower velocity
   - **Dormant (>72h):** don't reply in thread; consider DM
4. **Draft responses** for warm threads using `linkedin-reply-handler`.
5. **Flag suspicious patterns:**
   - Author replied but also deleted someone else's comment (author is actively moderating, tread carefully)
   - Commenter is in thread self-promoting (your reply shouldn't engage them)
6. **DM routing:** if thread is dormant but the author engaged meaningfully, draft a DM that references the thread specifically.

## Kevin Payne window

Named after the real 2026-04 data point: Kevin Payne (LawVu CEO) replied to Serge's comment 22h after the original post. This is the sweet spot.

- **0-6h:** 70% of author replies happen here if they're going to happen
- **6-24h:** ~25% of author replies, but these are higher-quality (author took time to think)
- **>24h:** thread rarely produces new author engagement

**Follow-up timing:**
- If author replied in 0-6h window: respond within 90 minutes
- If author replied in 6-24h window: respond within 2 hours (they're still checking)
- If author replied >24h: respond within 4 hours before thread goes cold

## Inbound-quality signals

High-quality commenter = worth the follow-up:
- Founder/operator title in profile
- Company in user's ICP
- Active posting history (not just reactions)
- Mutual 2nd-degree connections >10
- Prior thoughtful comments on user's posts

Low-quality = skip:
- Generic praise with no specifics
- Template language ("I'd love to hop on a quick call")
- Profile is sales/agency with no operator history
- Same comment across many creators' posts

## Hard rules

- Never reply to a reply later than 72h after the thread's last turn. Switch to DM.
- Never chain 3+ replies under one comment (thread spam).
- If the author deleted their reply, do not reply — they reconsidered.
- Don't DM a warm thread before first replying publicly (skips a step).

## Example

> Input: monitor sbulaev profile, last 24h

> Output:
> - **1 warm thread:** Kevin Payne replied 14h ago on LawVu post. Current stage: Warm (8-24h). Suggested response ready. Action: post within 2 hours.
> - 8 cold threads (no author engagement). Skip.
> - 3 watching threads (<6h old, author may still reply). Check again in 3-6h.

## Files

- `SKILL.md` — this file
- `references/thread-timing.md` — the timing matrix with examples

## Related skills

- `linkedin-reply-handler` — drafts the actual follow-up message
- `linkedin-comment-drafter` — drafts the initial comment that starts threads
