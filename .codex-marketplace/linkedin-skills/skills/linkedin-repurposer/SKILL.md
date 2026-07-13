---
name: linkedin-repurposer
description: Repurpose existing content into a native LinkedIn post. Take a tweet, thread, YouTube video, blog, or newsletter and rebuild it for LinkedIn: re-hook before the fold, expand to the 900 to 1300 char sweet spot, add whitespace and a CTA, move links to the first comment, run the humanizer, publish via Publora on approval. Not for writing from scratch (use linkedin-post-writer), not for auditing a draft (use linkedin-humanizer --mode audit).
---

# LinkedIn Repurposer

Turn something you already made into a post that reads like it was written for LinkedIn. Repurposing is not copy-paste. A tweet that flew on X will flop pasted into LinkedIn: too short, no whitespace, wrong rhythm, and a link in the body that tanks your reach.

This skill transforms, it does not generate. It reads your source, keeps the idea, and rebuilds the delivery for LinkedIn's 2026 algorithm.

## When to use

- "Turn this tweet / thread into a LinkedIn post"
- "Repurpose my YouTube video / blog / newsletter for LinkedIn"
- "This worked on Threads, adapt it for LinkedIn"
- "I have a rough idea in another format, make it native here"

Not for a blank-page draft (use `linkedin-post-writer`) and not for reviewing a finished LinkedIn draft (use `linkedin-humanizer --mode audit`).

## How it works

1. **Take the source.** Any format: a tweet or thread, a video or script, a blog paragraph, a caption, a transcript, a bullet list, a link to read. Ask for the source and the goal (comments / reposts / likes / saves) if not given.
2. **Extract the spine.** Strip the source platform's shell and pull out the one claim, story, or number worth keeping. Repurposing fails when it keeps the words instead of the point.
3. **Re-hook for LinkedIn.** The hook must land in the first 210 characters, before the "...see more" fold. The source's hook rarely survives; write a new first line using one of the 16 formulas in `../../references/hook-formulas.md`, picked by the goal.
4. **Expand to LinkedIn length.** X compresses; LinkedIn breathes. Grow the spine into the 900 to 1300 char sweet spot: short paragraphs, double line breaks between ideas, one concrete detail per beat. A dense tweet becomes 4 to 6 short paragraphs, not a wall.
5. **Add the LinkedIn shape.** Whitespace between ideas, a moment of real stakes or vulnerability (pure-insight posts do not land in 2026), and one clear closing question or CTA.
6. **Fix links and artifacts.** Move any external link to the first comment (in-body links suppress reach). Strip off-platform artifacts: hashtag walls, "link in bio", "smash subscribe", X @-handles, "as I tweeted" throat-clearing. 0 to 2 hashtags at the end.
7. **Humanizer pass.** Run the scrub: em dashes, AI vocab, rule-of-three, generic openers. Keep the user's real numbers and named entities from the source.
8. **Approval card.** Show: source -> LinkedIn mapping (what became what), formula used, char count, suggested posting window (Tue/Wed/Thu 7:30 to 9:00 AM local), the link-in-first-comment note.
9. **On approval.** Publish via `lib.publish(kind="post", draft_text=<approved>, target_url="https://www.linkedin.com/post/new/", platforms=[{"platform":"linkedin","platformId":<id>}], scheduled_time=<iso_or_None>)`. The wrapper handles Publora / manual / diy routing.

## Native-fit rules (source -> LinkedIn)

- **Tweet -> LinkedIn:** expand, do not paste. One tweet is a hook; grow the argument underneath it with whitespace.
- **X thread -> LinkedIn:** unroll into one flowing post, not a numbered list. Keep the best line as the hook.
- **YouTube video / script -> LinkedIn:** lead with the payoff, then the story of how you got there. Link the video in the first comment.
- **Blog / newsletter -> LinkedIn:** pick the single most quotable claim as the hook, then the one story that proves it. Do not summarize the whole piece.
- **Instagram / TikTok caption -> LinkedIn:** strip emoji density and hashtag blocks; add the professional stakes LinkedIn rewards.

## Hard rules

Global voice rules: see root `SKILL.md` §Voice rules. Additional skill-specific rules:

- Keep the source's **claim and facts** intact. Repurposing changes the delivery, never the meaning or the numbers.
- The hook must land in the first 210 characters, before the fold.
- Never paste the source and trim. Rebuild the hook, length, and rhythm from the spine.
- No external link in the post body. Offer to put it in the first comment.
- Include at least one moment of real stakes or vulnerability. Keep the source's real numbers and named entities.
- Do not name-drop the user's product as self-promo. One natural mention max.

## Anti-patterns (skill will refuse)

- Copy-pasting the source with light edits (that is not repurposing).
- Keeping the source platform's artifacts ("link in bio", "smash subscribe", hashtag walls).
- Shipping a tweet-length post with no whitespace or expansion.
- All-caps first line ("THIS CHANGED EVERYTHING").
- Em dashes anywhere.
- Rule-of-three lists without receipts.
- "leverage", "fundamentally", "game-changer", "deep dive".
- External links in the body.
- Meta throat-clearing ("I originally posted this on...").

## Resources

- `../../references/hook-formulas.md` - the 16 formula skeletons to re-hook with
- `../../references/algorithm-heuristics.md` - 2026 posting rules (timing, format, length)

## Related skills

- `linkedin-post-writer` - write a fresh post from scratch
- `linkedin-humanizer` - scrub AI tells, plus `--mode audit` to review the result
- `linkedin-hook-extractor` - reverse-engineer a hook from a post you admire
