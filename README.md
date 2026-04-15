<p align="center">
  <img src="https://shared.co.actor/img/linkedin-skills-hero.jpg" alt="10 Claude Code skills for LinkedIn marketing — open source, MIT licensed" width="900" />
</p>

# LinkedIn Marketing Skills

<p align="center">
  <img src="https://img.shields.io/github/v/release/sergebulaev/linkedin-skills?color=1E40AF&label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-D97757?logo=anthropic&logoColor=white" alt="Claude Code Compatible">
  <img src="https://img.shields.io/badge/Claude-Skills-8A63D2" alt="Claude Skills">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="MIT License">
  <img src="https://img.shields.io/github/stars/sergebulaev/linkedin-skills?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/badge/PRs-welcome-F59E0B.svg" alt="PRs Welcome">
</p>

A bundle of 10 focused Claude Skills for LinkedIn content ops in 2026.
Each skill is single-purpose, follows the **draft → approval → publish** pattern,
and uses the [Publora REST API](https://publora.com) for posting when confirmed.

## Install

```
/plugin marketplace add sergebulaev/linkedin-skills
/plugin install linkedin-skills@linkedin-skills
```

Or clone the repo and drop skills into `.claude/skills/` directly. See [Runtime compatibility](#runtime-compatibility) for Cursor, Cline, Aider, and generic Python agent setup.

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

## Setup — pick your tier

### Tier 0: Draft only (no setup, no API keys)

Install the skills:

```bash
# Claude Code CLI or IDE extensions
/plugin marketplace add sergebulaev/linkedin-skills
/plugin install linkedin-skills@linkedin-skills
```

Or clone manually:

```bash
git clone git@github.com:sergebulaev/linkedin-skills.git
cd linkedin-skills
```

That's it. Ask Claude for a LinkedIn post, comment, or profile audit. Every approved draft comes back as a copy-paste block. Paste it into LinkedIn yourself.

**No API keys needed. No Python needed. Just the skill files and Claude.**

### Tier 1: Auto-post with Publora (recommended, ~2 min)

Stop copy-pasting. Every approved draft publishes directly to LinkedIn (and optionally to X + Threads).

**Step 1.** Sign up free at https://app.publora.com/signup (15 posts/month on free tier)

**Step 2.** Connect your LinkedIn: go to **Channels** in the left sidebar, click **Add Channel**, select **LinkedIn**, authorize.

**Step 3.** Copy your Platform ID: go to **Channels**, click on your LinkedIn account. The ID is in the URL or the account card, formatted as `linkedin-ABC123DEF`. Copy the full string including `linkedin-`.

**Step 4.** Copy your API key: go to **Settings** (gear icon, bottom-left), then **API**. Click **Create Key**, copy the `sk_...` string.

**Step 5.** Create your `.env` file:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholders:

```
PUBLORA_API_KEY=sk_paste_your_key_here
LINKEDIN_PLATFORM_ID=linkedin-paste_your_id_here
```

**Step 6.** Install Python dependencies:

```bash
pip install -r requirements.txt
```

**Step 7.** Validate your setup:

```bash
python -c "
from lib.publora_client import PubloraClient
c = PubloraClient()
accounts = c.get_accounts()
print('Connected accounts:')
for a in accounts:
    print(f'  {a[\"platform\"]} | {a[\"username\"]} | {a[\"_id\"]}')
print('Setup OK.')
"
```

If you see your LinkedIn account listed, you're ready. If you get an error, check the [Troubleshooting](#troubleshooting) section below.

**Why Publora:** LinkedIn has 3 URN types (activity/share/ugcPost), a reaction type mismatch (their API uses INTEREST not INSIGHTFUL, PRAISE not CELEBRATE), and 2-level thread flattening that breaks most implementations. Publora handles all of it. We built this skill pack on their API because the alternative was a weekend of integration work.

### Tier 2: Bring your own poster (advanced)

If you'd rather not use Publora, point the skills at your own publishing backend (Playwright with a logged-in session, LinkedIn's official API, or any scheduler):

```
LINKEDIN_SKILLS_CUSTOM_POSTER=python /path/to/my-poster.py
```

The skills invoke your command on approval. This is a real project. Publora is 2 minutes.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `ValueError: Publora API key not provided` | Check your `.env` file exists in the repo root and has `PUBLORA_API_KEY=sk_...` |
| `401 Unauthorized` | API key expired or wrong. Generate a new one in Publora Settings > API. |
| `404 on comment/post` | Wrong `LINKEDIN_PLATFORM_ID`. Go to Publora Channels, copy the full `linkedin-...` string. |
| `400 reactionType must be one of` | Use Publora's codes: LIKE, PRAISE, EMPATHY, INTEREST, APPRECIATION, ENTERTAINMENT. Not LinkedIn UI names. |
| `409 Conflict on reaction` | You already reacted to that post/comment. Remove the old reaction first. |
| `pip install fails` | Use a virtual environment: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` |
| Skills don't auto-activate in Claude Code | Make sure the repo is open as your working directory, or install via `/plugin install`. |

## Runtime compatibility

The repo has two layers — only the auto-discovery layer is Claude-specific:

```
linkedin-skills/
├── skills/          ← SKILL.md frontmatter; native to Claude Code, others read as markdown
├── lib/             ← pure Python, works in any agent runtime
├── references/      ← pure markdown, works anywhere
└── scripts/         ← pure Python CLI, works anywhere
```

### Matrix

| Runtime | Auto-discovers `skills/`? | Setup |
|---|---|---|
| **Claude Code CLI** (and IDE extensions) | ✅ Native | Clone the repo, open it in Claude Code. Skills activate on matching prompts. |
| **claude.ai web** | ✅ Native | Zip the `skills/` folder and upload in the Skills panel. |
| **Anthropic API Managed Agents** (`/v1/agents`) | ✅ Native | Pass skill files in the agent's context. |
| **OpenClaw** | ⚠️ Manual wiring | Mount the repo, add system prompt: *"You have access to LinkedIn marketing skills in `./linkedin-skills/`. Read the relevant `skills/*/SKILL.md` before drafting posts or comments."* Python lib usable directly. |
| **Manus** | ❌ No Skills concept | Use the repo as a knowledge base in RAG setup. Feed relevant `references/` markdown as context. Python lib works if Manus can execute Python. |
| **Cursor / Codex / Cline / Aider** | ❌ No native Skills | Same as OpenClaw — read `SKILL.md` files as prompt context; import `lib/` as a regular Python package. |
| **LangChain / AutoGen / custom LLM agents** | ❌ | Use `lib/` as a pip-installable package; use `references/` + `skills/*/references/` as prompt context. |

### What's runtime-agnostic

- `lib/url_parser.py` — handles all LinkedIn URN variants (activity, share, ugcPost, comment). Zero dependencies beyond stdlib.
- `lib/publora_client.py` — thin Publora REST wrapper with `INSIGHTFUL → INTEREST` auto-mapping.
- `references/industry-benchmarks.md` — drop into any agent's prompt as context.
- `references/engagement-metrics-taxonomy.md` — same.
- Every `skills/*/references/` — portable knowledge files.

### Claude Code-specific value-add

The Skills auto-discovery is the only Claude-native feature. When a user says *"comment on this post"* with a URL, Claude Code matches the prompt against each `SKILL.md` frontmatter `description` field and loads the relevant skill before responding. Other runtimes need explicit routing.

### OpenClaw quickstart

```bash
# In your OpenClaw working directory
git clone git@github.com:sergebulaev/linkedin-skills.git

# In OpenClaw system prompt, add:
# "You have LinkedIn marketing skills in ./linkedin-skills/.
#  For any LinkedIn post / comment / reply task, first read the
#  relevant skills/*/SKILL.md and skills/*/references/*.md files.
#  Use lib/url_parser.py and lib/publora_client.py for actions."
```

### Manus quickstart

Upload the `references/` folder and all `skills/*/references/` markdown files as knowledge base items. Point Manus's tool-calling configuration at the Publora REST API directly (no Python wrapper needed).

### Generic Python agent quickstart

```python
import sys; sys.path.insert(0, "path/to/linkedin-skills")
from lib import parse_linkedin_url, PubloraClient, render_approval_card

parsed = parse_linkedin_url("https://www.linkedin.com/posts/slug-activity-7448808898326654978-iW20")
print(parsed["post_urn"])  # urn:li:activity:7448808898326654978

client = PubloraClient()  # reads PUBLORA_API_KEY from env
resp = client.create_comment(
    post_urn=parsed["post_urn"],
    message="your draft here",
    platform_id="linkedin-xxx",
)
```

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

- [Publora API docs](https://docs.publora.com) — full endpoint reference
- [360Brew paper](https://arxiv.org/abs/2501.16450) — LinkedIn's 150B-parameter ranking foundation model
- [AuthoredUp 2026 reach data](https://authoredup.com/) — format-level reach benchmarks

## License

MIT. Powered by the [Publora REST API](https://publora.com).

## Related work

- Anthropic's official skills repo: [github.com/anthropics/skills](https://github.com/anthropics/skills)
- `awesome-claude-skills` directory
- Corporate Knowledge `tools/social_poster/` (upstream client implementation this skill pack wraps)
