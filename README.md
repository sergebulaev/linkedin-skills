# LinkedIn Marketing Skills

A bundle of 10 focused Claude Skills for LinkedIn content ops in 2026.
Each skill is single-purpose, follows the **draft → approval → publish** pattern,
and uses the [Publora REST API](https://publora.com) for posting when confirmed.

## The skills

| Skill | Purpose | Input |
|---|---|---|
| [`linkedin-post-writer`](skills/linkedin-post-writer/) | Draft a viral-ready LinkedIn post using 10 proven 2026 hook formulas | topic, angle, audience |
| [`linkedin-comment-drafter`](skills/linkedin-comment-drafter/) | Draft a comment on any post from its URL | post URL |
| [`linkedin-reply-handler`](skills/linkedin-reply-handler/) | Draft a reply to any existing comment, handling LinkedIn's 2-level thread flattening | comment URL |
| [`linkedin-post-audit`](skills/linkedin-post-audit/) | Audit a draft against 360Brew algorithm + voice rules before publishing | draft text |
| [`linkedin-humanizer`](skills/linkedin-humanizer/) | Aggressively strip AI tells from any text | any text |
| [`linkedin-hook-extractor`](skills/linkedin-hook-extractor/) | Reverse-engineer the hook formula from any viral post | viral post URL |
| [`linkedin-content-planner`](skills/linkedin-content-planner/) | Generate a 7-day content plan with pillars, formulas, posting times, comment targets | theme, audience |
| [`linkedin-thread-engagement`](skills/linkedin-thread-engagement/) | Monitor threads for author replies (the Kevin Payne window) and draft follow-ups | profile URL |
| [`linkedin-profile-optimizer`](skills/linkedin-profile-optimizer/) | Audit and rewrite a LinkedIn profile end-to-end (headline, About, Featured, banner, Experience, Skills) | profile URL + goal |
| [`linkedin-employee-advocacy`](skills/linkedin-employee-advocacy/) | Plan, launch, and operate a team LinkedIn advocacy program (14-day launch, governance, ROI) | team size, goal |

## Cross-cutting references

- [`references/industry-benchmarks.md`](references/industry-benchmarks.md) — verified benchmarks across pharma, law, B2B SaaS, enterprise IT (engagement rates, time-per-post, reach multipliers)
- [`references/engagement-metrics-taxonomy.md`](references/engagement-metrics-taxonomy.md) — per-post / account-level / team-level / business-metric distinction

## The core pattern

Every action-taking skill follows three steps:

1. **Parse the input.** User provides a LinkedIn URL (post or comment). The shared `lib/url_parser.py` extracts the post URN and any comment ID.
2. **Draft the content.** The skill uses the 2026 research baked into its `references/` (hook formulas, algorithm heuristics, voice rules) to produce a draft and shows it to the user via `lib/approval.py`.
3. **Wait for approval.** The user replies with `post`, `yes`, or suggests edits. Only then does the skill call the Publora API to publish.

## Setup

```bash
git clone <this repo>
cd linkedin-skills
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in PUBLORA_API_KEY and LINKEDIN_PLATFORM_ID
```

### Get the credentials

- **PUBLORA_API_KEY:** sign up at [publora.com](https://publora.com) (free tier includes 15 LinkedIn + Bluesky posts/month). API key lives in the dashboard under `API`.
- **LINKEDIN_PLATFORM_ID:** in Publora dashboard, `Channels` → click your LinkedIn account → copy the ID (format: `linkedin-ABC123`).

## URL handling

LinkedIn has three post URN types; the parser handles all three:

| URL fragment | URN |
|---|---|
| `/posts/slug-activity-7448...` | `urn:li:activity:7448...` |
| `/posts/slug-share-7449...` | `urn:li:share:7449...` |
| `/feed/update/urn:li:ugcPost:7447...` | `urn:li:ugcPost:7447...` |

Comment URLs include a `commentUrn=urn:li:comment:(activity:POST,COMMENT)` query param; the parser decodes it and returns both `post_urn` and `comment_id`.

**Edge case:** the post URN inferred from the URL slug (e.g., `activity`) may not be the canonical URN LinkedIn uses (e.g., `ugcPost`). If `POST /linkedin-comments` returns 404, the skill falls back to resolving via an existing comment's `postId` field via HarvestAPI.

## Thread flattening

LinkedIn flattens reply threads to 2 levels. When replying to a reply, `parentComment` MUST point to the **top-level** comment URN, not the reply's URN. `linkedin-reply-handler` handles this correctly.

## Voice rules (baked into every skill)

1. No em dashes (`—`), en dashes, or double dashes. Biggest AI tell.
2. Use `..` for soft pauses when mid-sentence rhythm calls for it.
3. Capitalize personal names, company names, product names. Lowercase reads as disrespectful.
4. No AI vocabulary: `leverage`, `fundamentally`, `streamline`, `harness`, `delve`, `unlock`, `foster`.
5. Specific numbers beat adjectives.
6. One sharp insight per comment beats three vague ones.
7. 200-350 chars for comments, 900-1,300 chars for posts.

## Trying the parser

```bash
python lib/url_parser.py "https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20"
```

Returns a structured URN dict.

## References

- [Publora API docs](../publora.com/publora-api-docs/) — full endpoint reference
- [2026 viral drafts research](../corporate-knowledge/personal/knowledge/linkedin/serge/2026-04-13-viral-drafts/) — canonical hook formulas with engagement data
- [360Brew paper](https://arxiv.org/abs/2501.16450) — LinkedIn's 150B-parameter ranking foundation model
- [AuthoredUp 2026 reach data](https://authoredup.com/) — format-level reach benchmarks

## License

MIT. Powered by the [Publora REST API](https://publora.com).

## Related work

- Anthropic's official skills repo: [github.com/anthropics/skills](https://github.com/anthropics/skills)
- `awesome-claude-skills` directory
- Corporate Knowledge `tools/social_poster/` (upstream client implementation this skill pack wraps)
