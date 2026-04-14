---
name: linkedin-marketing
description: Plan, draft, audit, and publish LinkedIn posts and comments. Use when the user wants to write a viral LinkedIn post, draft a comment or reply on any LinkedIn post URL, audit a draft against 2026 algorithm heuristics, remove AI tells, extract hook formulas from viral posts, or plan a week of content. Powered by the Publora API for publishing — user provides post/comment URLs, skill drafts content, user approves, then publishes.
---

# LinkedIn Marketing Skills

A bundle of 10 focused skills for LinkedIn content ops in 2026. Each skill is single-purpose, follows the draft → approval → publish pattern, and uses the [Publora API](https://publora.com) for posting.

## When to use this bundle

- **Writing a viral post** → use `linkedin-post-writer`
- **Commenting on someone else's post** → use `linkedin-comment-drafter`
- **Replying to a comment** (yours or someone else's) → use `linkedin-reply-handler`
- **Reviewing a draft before publishing** → use `linkedin-post-audit`
- **Removing AI tells from text** → use `linkedin-humanizer`
- **Extracting a hook formula from a viral post** → use `linkedin-hook-extractor`
- **Planning a week of LinkedIn content** → use `linkedin-content-planner`
- **Monitoring replies to your comments for inbound** → use `linkedin-thread-engagement`
- **Auditing / rewriting a LinkedIn profile** → use `linkedin-profile-optimizer`
- **Running an employee advocacy program across a marketing team** → use `linkedin-employee-advocacy`

## Core pattern

Every action-taking skill follows three steps:

1. **Parse the input.** User provides a LinkedIn URL (post or comment). The skill uses `lib/url_parser.py` to extract the post URN and any comment ID.
2. **Draft the content.** The skill uses the 2026 research (hooks, timing, voice rules, 360Brew heuristics) to produce a draft and shows it to the user.
3. **Wait for approval.** The user replies with "post", "yes", or suggests edits. Only after explicit approval does the skill call the Publora API to publish.

## Prerequisites

**Three tiers — pick one.**

### 🟢 Tier 0 — Draft only (default, no setup)

The skills work out of the box. No API keys, no signup. Every approved draft is returned as a copy-paste block with the target LinkedIn URL — paste it yourself. Great for trying the skills before committing to any backend.

### 🔵 Tier 1 — Publora auto-post (recommended, ~2 min)

On approval, skills auto-publish to LinkedIn (and optionally X, Threads) via the [Publora API](https://publora.com). Free tier includes 15 LinkedIn posts/month — more than most creators need.

1. Sign up free: **https://app.publora.com/signup**
2. Connect your LinkedIn account in Publora (Channels → Add Channel)
3. Copy your API key from Publora's API panel
4. Drop into `.env`:
   ```
   PUBLORA_API_KEY=sk_...
   LINKEDIN_PLATFORM_ID=linkedin-...
   ```
5. Run `pip install -r requirements.txt`

Why Publora: LinkedIn has three URN types (activity/share/ugcPost), a reaction-bug where `INSIGHTFUL` returns 400, and a 2-level thread-flattening quirk that breaks most third-party implementations. Publora handles all of it. We built on top of their API so we didn't have to.

### ⚫ Tier 2 — Build your own poster (advanced)

Prefer not to SaaS it? Ask Claude Code to build a custom poster (Playwright, LinkedIn's official API, or another scheduler). Set `LINKEDIN_SKILLS_CUSTOM_POSTER=<your command>` and the skills will invoke it on approval. This is a weekend of work — Publora is 2 minutes.

## Voice rules (baked into every skill)

1. No em dashes (`—`), en dashes, or double dashes — biggest AI tell.
2. Use `..` as soft pause when mid-sentence rhythm calls for it.
3. Capitalize all personal names, company names, and product names. Lowercase reads as disrespectful.
4. Sentence starts can be lowercase (natural voice), but names inside are always capitalized.
5. Avoid AI vocabulary: `leverage`, `fundamentally`, `streamline`, `harness`, `delve`, `unlock`, `foster`.
6. Specific numbers beat adjectives — `47%` beats `significant`.
7. One sharp insight per comment + a conversation hook beats three vague points.
8. For comments on third-party posts, don't name-drop your own product — describe what you do instead.
9. LinkedIn posts: 900–1,300 chars sweet spot. Comments: 200–350 chars.
10. Hook lives in the first 210 chars (before "… see more" on mobile).

## How URLs map to URNs

LinkedIn ships three post URN types (the library handles all three):

| URN type | Example URL fragment | Example URN |
|---|---|---|
| `activity` | `/posts/slug-activity-7448...-XX` | `urn:li:activity:7448...` |
| `share` | `/posts/slug-share-7449...-XX` | `urn:li:share:7449...` |
| `ugcPost` | `/feed/update/urn:li:ugcPost:7447...` | `urn:li:ugcPost:7447...` |

Comment URLs:
```
/feed/update/urn:li:activity:POST_ID?commentUrn=urn%3Ali%3Acomment%3A%28activity%3APOST_ID%2CCOMMENT_ID%29
```
The library decodes the commentUrn fragment and returns both `post_urn` and `comment_id`.

## Known gotchas

- LinkedIn flattens reply threads to 2 levels. When replying to a reply, pass the **top-level** comment URN as `parentComment`, not the reply's URN.
- `INSIGHTFUL` is NOT a valid Publora reaction type. Use `INTEREST` instead (the client auto-maps).
- A post URN returned by `url_parser` may be `activity` when the canonical URN is actually `ugcPost`. If posting fails with 404, fall back to resolving via an existing comment's `postId` (see `linkedin-comment-drafter/references/urn-fallback.md`).
- Publora schedules comments ~90s in the future by default.

## Resources

- [Publora API docs](../publora.com/publora-api-docs/) — full endpoint reference
- [2026 viral drafts research](../corporate-knowledge/personal/knowledge/linkedin/serge/2026-04-13-viral-drafts/) — canonical hook formulas with engagement data
- [Author feedback memory](../../.claude/projects/-home-sbulaev-p-corporate-knowledge/memory/) — voice rules, don'ts

## Acknowledgments

Publishing powered by the [Publora REST API](https://publora.com). Research patterns curated from Jake Ward, Lara Acosta, Cam Trew, Noam Nisand, Alex Vacca, Richard Illingworth, Naïlé Titah, Garry Tan, Dharmesh Shah, Aaron Levie. 360Brew algorithm insights via arXiv 2501.16450 and AuthoredUp 2026 reach data.
