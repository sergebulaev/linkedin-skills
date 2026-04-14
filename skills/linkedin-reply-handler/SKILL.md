---
name: linkedin-reply-handler
description: Draft a reply to any existing LinkedIn comment from a URL. Use when the user wants to reply to a comment on someone else's post, reply to a reply on their own post, or follow up in a thread where the author just responded. The skill parses the commentUrn from the URL, figures out the correct parentComment target (LinkedIn flattens threads to 2 levels), drafts the reply in the user's voice, and waits for approval before posting via Publora. Keywords: linkedin reply, reply to comment, thread continuation, comment URL, parent comment URN.
---

# LinkedIn Reply Handler

Drafts a reply to a specific LinkedIn comment. Correctly handles LinkedIn's 2-level thread flattening: if you're replying to a reply, the Publora API needs the TOP-level comment URN as `parentComment`, not the reply's URN.

## When to use

- User pastes a LinkedIn comment URL (contains `?commentUrn=...`) and says "reply to this"
- An author (e.g., Kevin Payne, Felix Tseitlin) replied to the user's comment and the user wants to continue the thread
- User wants to re-engage a conversation that's gone dormant

## Input

A LinkedIn URL containing `commentUrn=urn:li:comment:(activity:POST,COMMENT_ID)` — either the direct comment permalink or a feed URL with the query fragment.

## Output

- 1-2 reply drafts, 150-300 chars each
- Reaction suggestion for the comment being replied to (always react before replying)
- Thread context summary (who said what, when)
- Approval card → on user "post", fires reaction + reply via Publora

## Steps

1. **Parse the URL.** `lib.url_parser.parse_linkedin_url` returns `post_urn`, `comment_id`, `comment_urn`.
2. **Determine thread structure.** Fetch the post's comment thread (HarvestAPI if available) and locate the comment. Figure out whether it's:
   - a top-level comment (parentComment = this comment's URN when replying)
   - a reply to a top-level comment (parentComment = the TOP comment's URN, not this reply's URN — LinkedIn flattens)
3. **Read the full context.** Author post text, top-level comment text, any intermediate replies. Include the user's own prior comment if they're in the thread.
4. **Draft the reply.** Follow the engagement templates in `references/reply-templates.md`. If the counterpart asked a question, answer it directly. If they pushed back, concede then sharpen.
5. **Humanizer pass.** Strip em dashes, AI vocab, enforce varied sentence length.
6. **Approval card.** Include thread preview (who said what in last 3 turns), the draft, reaction suggestion, and the parentComment URN we'll send.
7. **On approval — adapt to the active backend.** Call `lib.active_backend()`:
   - **`publora`** (PUBLORA_API_KEY set) → react on the specific comment being replied to, pause 8-15s, then post reply with the correct top-level `parentComment` URN.
   - **`manual`** (no backend configured — the default) → output the approved reply via `lib.manual_mode_message(draft_text, target_url, kind="reply")`. Include the parent comment URL so the user knows exactly where to paste. Do NOT attempt to post.
   - **`diy`** (LINKEDIN_SKILLS_CUSTOM_POSTER set) → invoke the custom poster with draft, target URL, and parent-comment URN.

## The flattening gotcha

LinkedIn only nests replies two levels deep. Visually the thread looks like:

```
Top comment by Alice (id: 111)
└─ Reply by Bob (id: 222)          ← parentComment: urn:li:comment:(activity:POST, 111)
   └─ Reply by Carol (id: 333)     ← parentComment: STILL urn:li:comment:(activity:POST, 111)
```

Carol's reply doesn't nest under Bob's — it's pinned at level 2 to the same top comment. If you pass `urn:li:comment:(activity:POST, 222)` as parentComment, the API returns 400 on some paths or silently misplaces the reply.

**Rule in this skill:** always use the TOP-level comment's URN as `parentComment`. If you're replying to a 2nd-level reply, we walk up the tree to find the top comment.

## Templates (`references/reply-templates.md`)

- **R1 Answer-Their-Question** — they asked, you answer plainly + one real detail
- **R2 Concede-Then-Sharpen** — "you're right on X, and the piece I'd push on is Y"
- **R3 Extend-Their-Thesis** — take their point one layer deeper with a new framing
- **R4 Share-Lived-Experience** — "we hit this last quarter — here's what broke"
- **R5 Ask-Back** — redirect with a sharper question when their position needs more context

## Hard rules

- 150-300 chars. Replies are tighter than top-level comments.
- React to the comment you're replying to, not to the parent post.
- Capitalize the counterpart's first name.
- Never paste a canned "thanks!" — either respond with content or don't reply.
- If the thread is older than 72 hours, consider a DM instead (use `linkedin-thread-engagement`).

## Example

> User: "Reply to this: https://www.linkedin.com/feed/update/urn:li:activity:7449018753880834048?commentUrn=urn%3Ali%3Acomment%3A%28activity%3A7449018753880834048%2C7449758545140453376%29"
>
> Skill: parses → post 7449018753880834048, comment 7449758545140453376. Fetches thread. Sees: Kevin Payne's post → Serge's comment ("moat moved to taste") → Kevin's reply ("How are you building that conviction muscle with your team?"). Drafts R1 Answer-Their-Question variant. Shows approval card.
>
> User: "post"
>
> Skill: react APPRECIATION on Kevin's reply → pause 12s → post reply with parentComment set to Serge's original comment URN (the TOP level, not Kevin's reply).

## Files

- `SKILL.md` — this file
- `references/reply-templates.md` — 5 reply templates with examples
- `references/threading-rules.md` — LinkedIn's 2-level flattening explained with edge cases
