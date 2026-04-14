---
name: linkedin-comment-drafter
description: Draft a high-quality LinkedIn comment on any post from a URL. Use when the user gives a LinkedIn post URL and asks to comment on it. The skill parses the URL, reads the post context, drafts 1-3 comment variants in the user's voice using 2026 hook patterns (first-commenter, data-first, answer-the-closing-question, quotable-reframe), picks a reaction type, and waits for approval before posting via Publora. Keywords: linkedin comment, engage post, comment draft, first commenter, linkedin reply strategy.
---

# LinkedIn Comment Drafter

Produce conversation-provoking comments on any LinkedIn post from a URL. The skill targets the patterns that actually got author replies in 2026 testing (Kevin Payne / Ivan Tsybaev patterns) and avoids the thesis-restatement patterns that die with zero engagement.

## When to use

- User pastes a LinkedIn post URL and says "comment on this", "draft me a comment", "engage with this post"
- User wants to be among the first 3 commenters on a viral post
- User wants to reply to a closing question the author asked

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
2. **Fetch the post body.** If HarvestAPI is available via `corporate-knowledge/personal/knowledge/tools/social_poster/src/harvest_client.py`, pull the post text and top 3 existing comments (to avoid duplicate takes). If not, ask the user to paste the post text.
3. **Detect the author's closing question.** If the post ends with a "?" line, the Answer-the-Closing-Question template usually wins.
4. **Draft comment variants.** Pick 2-3 templates from `references/comment-templates.md` that fit the post's topic. Fill them with user-voice phrasing.
5. **Run the humanizer pass.** Strip em dashes, AI vocab, uniform sentence rhythm. Add a specific number or named entity if missing.
6. **Present drafts for approval** using `lib.approval.render_approval_card`. Include: target URL, each variant, reaction suggestion, a one-line "why this template fits".
7. **On approval — adapt to the active backend.** Call `lib.active_backend()`:
   - **`publora`** (PUBLORA_API_KEY set) → react to the post with the chosen reaction type, pause 8-15s, then post via `lib.PubloraClient.create_comment` (top-level, no `parent_comment`). Return the comment URN.
   - **`manual`** (no backend configured — the default) → output the approved draft via `lib.manual_mode_message(draft_text, target_url, kind="comment")`. This gives the user a copy-paste block plus a one-time setup prompt for Publora (the preferred auto-post path). Do NOT attempt to post programmatically.
   - **`diy`** (LINKEDIN_SKILLS_CUSTOM_POSTER set) → invoke the user's configured custom poster command with the draft text + target URL as arguments.

## Templates (see `references/comment-templates.md` for full list)

- **T1 Missing-Piece** (Kevin Payne pattern, highest hit rate): `[Name] the [their-thesis] argument misses one piece.. [what-moved]. when [their-condition], the real differentiator is [specific-skill], not [their-focus].`
- **T2 Answer-the-Closing-Question**: direct answer + one concrete example + why it matters
- **T3 Data-First**: `half the [population] I see now [behavior]. the [old-assumption] broke around [date]. [new-rule].`
- **T4 Practitioner Observation**: `when X the system does Y, when X' it does Y'. that's when [outcome] kicks in.`
- **T5 Counter-with-Concession**: agree on point 1, push back on point 2 with one rooted reason
- **T6 Quotable-Reframe**: one line under 12 words + expansion
- **T7 Ask-a-Sharper-Question**: `the harder version of this question is..`

## Hard rules

- 200-350 chars. Don't exceed.
- Always capitalize the author's name (e.g., "Dharmesh", not "dharmesh").
- No em dashes, no hashtags, no emoji unless the post itself uses them.
- No mention of the user's own product by name. Describe what they do instead.
- Never paste generic praise ("Great post!", "This.", "100%"). The skill refuses.
- Skip the comment if the post is sponsored, a generic listicle, or the author has already deleted it.

## Example invocation

> User: "Comment on this: https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20"
>
> Skill: [parses URL, fetches post, detects closing question "Seen this in your market?", drafts 3 variants]
>
> Skill returns: T2 Answer-the-Closing-Question variant as primary pick, with T1 Missing-Piece as backup, reaction `INTEREST`, one-line rationale, and approval prompt.

## Files in this skill

- `SKILL.md` — this file
- `references/comment-templates.md` — the 7 templates with fill-in slots and real examples
- `references/voice-rules.md` — the specific voice rules from user feedback memories

## Related skills

- `linkedin-reply-handler` — if you're replying to a comment (not posting top-level)
- `linkedin-humanizer` — for aggressive AI-tell scrubbing
- `linkedin-hook-extractor` — if you want to use the author's own hook as the basis for your reply
