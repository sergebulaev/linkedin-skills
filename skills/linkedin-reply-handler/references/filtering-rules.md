# Filtering rules — what gets dropped before drafting a whole-thread sweep

The whole point of a full-thread sweep is that not every comment deserves a reply. Drafting one anyway produces the exact "thanks!" filler this skill's hard rules already ban. Run every fetched comment through these checks before it enters the reply queue.

## Drop: generic praise, no content

No specific claim, question, or detail to respond to. Pattern-match (case-insensitive, whole comment after trimming emoji/punctuation):

- "great post", "great share", "love this", "so true", "this!", "100%", "well said", "spot on", "nailed it", "facts", "🔥" / "👏" alone or repeated
- Single-word or single-emoji comments with nothing else
- Comments under ~4 words with no question mark and no named detail

A short comment that references something specific ("this happened to us in March too") is not generic praise — the length rule only applies when there's also nothing to respond to.

## Drop: duplicate or near-duplicate text

If two or more comments in the thread are the same template phrase (a common pattern on posts with 50+ comments: engagement pods, copy-paste "insightful post!" from low-effort accounts), reply to at most one and note the rest as duplicates in the filter summary rather than drafting N near-identical replies.

## Drop: spam / engagement-bait

- Comments that are just a link with no context, or "check my profile" / "DM me" self-promotion unrelated to the post's topic
- Comments copy-pasted verbatim across many different authors' posts (if `fetch_post_comments` or prior context reveals this pattern)
- Comments whose only content is tagging other people with no accompanying text

## Drop: the user's own comments

Any comment authored by the account running this skill (match by profile URL or name against the user's own LinkedIn identity). Never draft a reply to yourself.

## Keep, always

- Any comment ending in a question mark
- Any comment that disagrees, pushes back, or adds a counterpoint
- Any comment with a named detail, number, or specific example — even if short
- Any comment from someone who has commented on the user's posts before (worth continuing the relationship even if this specific comment is thin) — flag these as "keep: relationship" rather than auto-filtering on length alone

## Reporting the filter pass

Show the user counts, not just a final list: "23 comments fetched → 6 filtered (4 generic praise, 1 duplicate, 1 spam link) → 17 drafted." This is what lets the user sanity-check the sweep before approving, since they can't review 23 raw comments themselves in the same time it takes to read 17 drafts.
