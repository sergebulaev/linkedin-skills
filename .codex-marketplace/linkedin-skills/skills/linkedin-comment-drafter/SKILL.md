---
name: linkedin-comment-drafter
description: Draft a LinkedIn comment on someone else's post from its URL, or reshare (repost) it to your feed with optional commentary. Use when the user pastes a post URL and asks to comment, engage, be first commenter, or repost with their thoughts. Produces 1-3 variants in the user's voice, picks a reaction, and publishes via Publora on approval. Not for replying to existing comments (use linkedin-reply-handler).
---

# LinkedIn Comment Drafter

Produce conversation-provoking comments on any LinkedIn post from a URL. The skill targets the patterns that actually got author replies in 2026 testing and avoids the thesis-restatement patterns that die with zero engagement.

## When to use

- User pastes a LinkedIn post URL and says "comment on this", "draft me a comment", "engage with this post"
- User wants to be among the first 3 commenters on a viral post
- User wants to reply to a closing question the author asked
- User wants to **reshare/repost** a post to their own feed, with or without a one-line take ("repost this with my thoughts", "reshare this")

## Input

A LinkedIn post URL in any of the standard shapes (see the top-level `SKILL.md` URL table).

## Output

1-3 draft comment variants, each with:
- 200-350 char body, 1-2 short paragraphs, no em dashes, no hashtags
- Assigned reaction type: `LIKE`, `PRAISE`, `EMPATHY`, `INTEREST`, `APPRECIATION`, or `ENTERTAINMENT`
- Pattern label (which of the 7 templates was used)
- Estimated engagement fit based on what the author typically responds to

Then waits for user approval. On "post", calls Publora to react + comment.

## Steps

1. **Parse the URL.** Use `lib.url_parser.parse_linkedin_url` to get `post_urn` and, if present, the post's activity ID.
2. **Fetch the post body.** If `APIFY_TOKEN` is set, call `lib.ApifyClient.fetch_post(url)` for the post body and `fetch_post_comments(post_id=..., max_items=10)` for the top existing comments (so your draft doesn't duplicate an existing take). Both actors are no-cookies and cost roughly $0.001 + $0.005 per call on the Apify free tier. If `APIFY_TOKEN` is not set, ask the user to paste the post text and (optionally) top comments.
3. **Detect the author's closing question.** If the post ends with a "?" line, the Answer-the-Closing-Question template usually wins.
4. **Draft comment variants.** Pick 2-3 templates from `references/comment-templates.md` that fit the post's topic. Fill them with user-voice phrasing.
5. **Run the humanizer pass.** Strip em dashes, AI vocab, uniform sentence rhythm. Add a specific number or named entity if missing.
6. **Present drafts for approval** using `lib.approval.render_approval_card`. Include: target URL, each variant, reaction suggestion, a one-line "why this template fits".
7. **On approval.** Call `lib.publish(kind="comment", draft_text=<approved>, target_url=<post_url>, post_urn=<urn>, platform_id=<id>, reaction_type=<chosen>)`. The wrapper handles Publora / manual / diy routing.

## Reshare mode (repost with your thoughts)

Same input as commenting (a post URL), but instead of commenting on the post you
reshare it to the user's own feed, optionally with a short take above it. Use
this when the ask is "repost", "reshare", or "share this with my network".

1. **Fetch the post** the same way (`lib.fetch_post(url)`), and check it is
   reshareable: the Apify payload exposes `canShare` and the `shareUrn`
   (`urn:li:share:*` / `urn:li:ugcPost:*`). If `canShare` is `False`, tell the
   user the author disabled resharing and stop.
2. **Draft the commentary** (optional). Keep it to one or two sentences in the
   user's voice: a genuine take, endorsement, or the reason this is worth a
   colleague's time. Run the same humanizer pass (no em dashes, no AI vocab). A
   plain reshare with no commentary is also valid; skip the draft if the user
   just wants to amplify.
3. **Present for approval** with the original post URL and the drafted commentary
   (or "plain reshare, no commentary").
4. **On approval.** Call `lib.repost(post_url, commentary=<approved or None>)`.
   The wrapper resolves the correct `shareUrn` from Apify (do not hand-convert an
   `activity` id, the share id can differ), refuses posts with resharing off, and
   routes Publora / manual / diy. Manual tier returns copy-paste steps ("Repost
   with your thoughts"). The new reshare URN is `result["reshare"]["id"]`.

Commentary cap is 3000 chars (LinkedIn), but a tight one or two sentences
outperforms a wall of text. This is the tool `linkedin-employee-advocacy` uses
to reshare brand and colleague posts.

## Templates (see `references/comment-templates.md` for full list)

- **T1 Missing-Piece** (highest hit rate): `[Name] the [their-thesis] argument misses one piece.. [what-moved]. when [their-condition], the real differentiator is [specific-skill], not [their-focus].`
- **T2 Answer-the-Closing-Question**: direct answer + one concrete example + why it matters
- **T3 Data-First**: `half the [population] I see now [behavior]. the [old-assumption] broke around [date]. [new-rule].`
- **T4 Practitioner Observation**: `when X the system does Y, when X' it does Y'. that's when [outcome] kicks in.`
- **T5 Counter-with-Concession**: agree on point 1, push back on point 2 with one rooted reason
- **T6 Quotable-Reframe**: one line under 12 words + expansion
- **T7 Ask-a-Sharper-Question**: `the harder version of this question is..`

## Hard rules

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules:

- 200-350 chars. Don't exceed.
- Always capitalize the author's name when addressing them by first name.
- No hashtags, no emoji unless the post itself uses them.
- No mention of the user's own product by name. Describe what they do instead.
- Never paste generic praise ("Great post!", "This.", "100%"). The skill refuses.
- Skip the comment if the post is sponsored, a generic listicle, or the author has already deleted it.

## Example invocation

> User: "Comment on this: https://www.linkedin.com/posts/<author-handle>_activity-<id>"
>
> Skill: [parses URL, fetches post, detects closing question "Seen this in your market?", drafts 3 variants]
>
> Skill returns: T2 Answer-the-Closing-Question variant as primary pick, with T1 Missing-Piece as backup, reaction `INTEREST`, one-line rationale, and approval prompt.

## Files in this skill

- `SKILL.md` — this file
- `references/comment-templates.md` — the 7 templates with fill-in slots and real examples
- `../../references/voice-rules.md` — the specific voice rules from user feedback memories

## Related skills

- `linkedin-reply-handler` — if you're replying to a comment (not posting top-level)
- `linkedin-humanizer` — for aggressive AI-tell scrubbing
- `linkedin-hook-extractor` — if you want to use the author's own hook as the basis for your reply
- `linkedin-employee-advocacy` — the program that uses reshare mode to amplify brand and colleague posts across a team
