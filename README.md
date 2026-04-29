<p align="center">
  <img src="https://shared.co.actor/img/linkedin-skills-hero.jpg" alt="10 Claude Code skills for LinkedIn marketing — open source, MIT licensed" width="900" />
</p>

# LinkedIn Marketing Skills for Claude

<p align="center">
  <img src="https://img.shields.io/github/v/release/sergebulaev/linkedin-skills?color=1E40AF&label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-D97757?logo=anthropic&logoColor=white" alt="Claude Code Compatible">
  <img src="https://img.shields.io/badge/Claude-Skills-8A63D2" alt="Claude Skills">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="MIT License">
  <img src="https://img.shields.io/github/stars/sergebulaev/linkedin-skills?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/badge/PRs-welcome-F59E0B.svg" alt="PRs Welcome">
</p>

10 skills that help Claude write LinkedIn posts, comments, and replies in your voice. They draft content, strip AI tells, and wait for your approval before anything gets published. No coding required.

## Install

Pick whichever way you use Claude:

### claude.ai (web)

1. Open https://claude.ai/code
2. Go to **Skills** in the sidebar
3. Click **Add from GitHub**
4. Paste: `sergebulaev/linkedin-skills`
5. Done. The skills activate automatically when you ask about LinkedIn.

### Claude Desktop (Mac / Windows)

1. Open Claude Desktop
2. Open **Settings** (gear icon)
3. Go to **Skills**
4. Click **Add from GitHub**
5. Paste: `sergebulaev/linkedin-skills`
6. Done. Start a new conversation and ask Claude to write a LinkedIn post.

### OpenClaw

1. Open your OpenClaw working directory
2. Clone the skills into it:
   ```bash
   git clone https://github.com/sergebulaev/linkedin-skills.git
   ```
3. In OpenClaw settings, add this to your system prompt:
   ```
   You have LinkedIn marketing skills in ./linkedin-skills/.
   For any LinkedIn task, read the relevant skills/*/SKILL.md first.
   Use lib/url_parser.py for URL parsing,
       lib/apify_client.py for reading posts / comments / engagers,
       lib/publora_client.py for publishing actions.
   ```
4. Done. Ask OpenClaw to write a LinkedIn post or comment.

### Claude Code (CLI / VS Code / JetBrains)

```
/plugin marketplace add sergebulaev/linkedin-skills
/plugin install linkedin-skills@linkedin-skills
```

Or clone the repo and open it as your working directory:

```bash
git clone https://github.com/sergebulaev/linkedin-skills.git
cd linkedin-skills
```

## What you can do

Once installed, just talk to Claude. The right skill activates automatically.

**Write a post:**
> "Write me a LinkedIn post about why AI agencies are replacing traditional ones. Make it viral."

**Comment on someone's post:**
> "Comment on this post: https://linkedin.com/posts/... — I want to add a thoughtful take."

**Check a draft before publishing:**
> "Audit this post draft for AI tells and algorithm issues: [paste your text]"

**Reverse-engineer a viral post:**
> "What hook formula does this post use? https://linkedin.com/posts/..."

**Plan your week:**
> "Create a 7-day LinkedIn content plan. I'm a B2B SaaS founder targeting VPs of Marketing."

**Rewrite your profile:**
> "Optimize my LinkedIn profile for inbound leads: https://linkedin.com/in/yourname"

**Remove AI tells from any text:**
> "Humanize this text: [paste AI-generated draft]"

Every skill shows you a draft first and waits for your OK before doing anything. Nothing gets posted without your approval.

## The 10 skills

| Skill | What it does |
|---|---|
| **Post Writer** | Drafts viral-ready posts using 10 proven 2026 hook formulas (anaphora, R.I.P. obituary, year-over-year pivot, curiosity gap, and 6 more) |
| **Comment Drafter** | Drafts a comment on any LinkedIn post from its URL |
| **Reply Handler** | Drafts a reply to any comment, correctly handling LinkedIn's 2-level thread flattening |
| **Post Audit** | Checks your draft against 2026 algorithm rules and AI-detection patterns before you publish |
| **Humanizer** | Strips em dashes, AI vocabulary ("leverage", "delve", "harness"), rule-of-three lists, and other AI fingerprints. Bundles three sub-tools: AI-emoji density scorer, multi-detector spread tester (GPTZero, Originality.ai, ZeroGPT, Sapling, Copyleaks), and a rule-explainer reference for defending stylistic choices. |
| **Hook Extractor** | Reverse-engineers the hook formula from any viral post. Returns a blank template you can fill with your own topic |
| **Content Planner** | Creates a 7-day plan with daily post topics, formats, hooks, posting times, and comment targets |
| **Engagement Monitor** | Two read-side workflows: (1) tracks your comment threads for author replies and drafts follow-ups in the 6-24h window; (2) pulls likers and commenters on any post and groups them by ICP fit (peer / aspirational / prospect). |
| **Profile Optimizer** | Rewrites your headline, About section, Featured section, and Experience for 2026 conversion patterns |
| **Employee Advocacy** | Plans a team LinkedIn program: 14-day launch, posting cadence, brand governance, ROI tracking |

## Optional: read LinkedIn data with Apify

Four of the skills (Comment Drafter, Reply Handler, Hook Extractor, Engagement Monitor) can read post bodies, comment threads, your own recent comments, and the people who liked or commented on any post. Without an Apify token they fall back to asking you to paste the relevant text. With one, they fetch automatically.

[Apify](https://console.apify.com/sign-up) free tier ships with $5/month of credit, which goes a long way at $1-$5 per 1,000 results. The skills use four no-cookies actors:

| Use case | Actor | Cost |
|---|---|---|
| Post body by URL | `supreme_coder/linkedin-post` | $1 / 1,000 |
| Comments + replies on a post | `apimaestro/linkedin-post-comments-replies-engagements-scraper-no-cookies` | $5 / 1,000 |
| Your own recent comments | `apimaestro/linkedin-profile-comments` | $5 / 1,000 |
| Likers + commenters on any post | `scraping_solutions/linkedin-posts-engagers-likers-and-commenters-no-cookies` | $5 / 1,000 |

Setup: drop `APIFY_TOKEN=apify_api_...` into your `.env`. The thin client at `lib/apify_client.py` exposes `fetch_post`, `fetch_post_comments`, `fetch_user_recent_comments`, and `fetch_post_engagers`.

A typical creator running daily comment ops + a weekly engager-analytics sweep stays under $2/month, well inside the free tier.

## Optional: auto-post with Publora

By default, skills draft content for you to copy-paste into LinkedIn. If you want Claude to publish directly to your LinkedIn (and optionally to X, Threads, Instagram), connect Publora. It takes about 2 minutes.

### What is Publora?

[Publora](https://publora.com) is a publishing API that handles LinkedIn's quirks (3 different URL formats, reaction type mismatches, thread flattening bugs). The free tier gives you 15 posts/month.

### Setup (2 minutes)

**Step 1.** Sign up at https://app.publora.com/signup (free)

**Step 2.** Connect LinkedIn: click **Channels** in the left sidebar, then **Add Channel**, pick **LinkedIn**, authorize.

**Step 3.** Find your Platform ID: go to **Channels**, click your LinkedIn account. The ID looks like `linkedin-ABC123DEF`. Copy the whole thing including `linkedin-`.

**Step 4.** Get your API key: click **Settings** (gear icon, bottom-left), then **API**, then **Create Key**. Copy the `sk_...` string.

**Step 5.** Create a file called `.env` in the linkedin-skills folder:

```
PUBLORA_API_KEY=sk_paste_your_key_here
LINKEDIN_PLATFORM_ID=linkedin-paste_your_id_here
```

If you cloned the repo, you can copy the template instead:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholders with your real values.

**Step 6.** Install two small Python packages:

```bash
pip install requests python-dotenv
```

**Step 7.** Test it. Ask Claude:

> "Schedule a test LinkedIn post via Publora 2 hours from now: 'testing the API connection'. Show me the response, then delete it."

If Publora returns a scheduled-post ID, you're set. If you get HTTP 401, your API key is wrong. If you get HTTP 400 about a missing platformId, your `LINKEDIN_PLATFORM_ID` isn't set. See [Troubleshooting](#troubleshooting).

## Voice rules

Every skill follows these rules automatically:

1. No em dashes. Biggest AI tell in 2026.
2. Capitalize names. Always. Lowercase reads as disrespectful.
3. No AI vocabulary: "leverage", "fundamentally", "streamline", "harness", "delve", "unlock", "foster".
4. Specific numbers beat adjectives. "$14,200" beats "significant savings".
5. One sharp insight per comment beats three vague ones.
6. 200-350 chars for comments, 900-1,300 chars for posts.

## Troubleshooting

| Problem | Fix |
|---|---|
| Skills don't activate when I ask about LinkedIn | Make sure you installed via the Skills panel or `/plugin install`. Try starting a new conversation. |
| "Publora API key not provided" | Your `.env` file is missing or in the wrong folder. It should be in the `linkedin-skills/` root. |
| "401 Unauthorized" from Publora | Your API key expired. Go to Publora Settings > API > Create a new key. |
| "404 on comment/post" | Your `LINKEDIN_PLATFORM_ID` is wrong. Go to Publora Channels and copy the full `linkedin-...` string. |
| "400 reactionType" error | Known Publora quirk. The skills handle this automatically. If you're calling the API manually, use PRAISE (not CELEBRATE), INTEREST (not INSIGHTFUL). |
| `pip install` fails | Use a virtual environment: `python -m venv venv && source venv/bin/activate && pip install requests python-dotenv` |

## Cross-cutting references

- [`references/industry-benchmarks.md`](references/industry-benchmarks.md) — engagement rates, time-per-post, reach multipliers across industries
- [`references/engagement-metrics-taxonomy.md`](references/engagement-metrics-taxonomy.md) — what to measure at post / account / team / business level

---

<details>
<summary><b>For developers: runtime compatibility, URL parsing, and internals</b></summary>

## Runtime compatibility

```
linkedin-skills/
├── skills/          ← SKILL.md frontmatter; native to Claude Code, others read as markdown
├── lib/             ← pure Python, works in any agent runtime
├── references/      ← pure markdown, works anywhere
└── scripts/         ← pure Python CLI, works anywhere
```

| Runtime | Auto-discovers skills? | Setup |
|---|---|---|
| **Claude Code** (CLI, Desktop, Web, IDE) | Yes | Install via plugin or clone. Skills activate on matching prompts. |
| **Anthropic Managed Agents** (`/v1/agents`) | Yes | Pass skill files in the agent context. |
| **OpenClaw** | Manual | Mount the repo, add system prompt pointing to `skills/*/SKILL.md`. |
| **Cursor / Codex / Cline / Aider** | No | Read `SKILL.md` files as prompt context; import `lib/` as Python. |
| **Manus** | No | Upload `references/` as knowledge base. Call Publora API directly. |
| **LangChain / AutoGen** | No | Use `lib/` as a package; feed `references/` as prompt context. |

### OpenClaw quickstart

```bash
git clone git@github.com:sergebulaev/linkedin-skills.git

# Add to OpenClaw system prompt:
# "You have LinkedIn marketing skills in ./linkedin-skills/.
#  Read the relevant skills/*/SKILL.md before any LinkedIn task.
#  Use lib/url_parser.py for URL parsing,
#      lib/apify_client.py for reading posts / comments / engagers,
#      lib/publora_client.py for publishing."
```

### Generic Python agent quickstart

```python
import sys; sys.path.insert(0, "path/to/linkedin-skills")
from lib import parse_linkedin_url, PubloraClient, ApifyClient

parsed = parse_linkedin_url("https://www.linkedin.com/posts/slug-activity-7448808898326654978-iW20")
print(parsed["post_urn"])  # urn:li:activity:7448808898326654978

# Read side (Apify)
apify = ApifyClient()  # reads APIFY_TOKEN from env
post = apify.fetch_post(post_url="https://www.linkedin.com/posts/...")
engagers = apify.fetch_post_engagers(post_url="https://www.linkedin.com/posts/...", max_items=50)

# Write side (Publora)
client = PubloraClient()  # reads PUBLORA_API_KEY from env
client.create_comment(post_urn=parsed["post_urn"], message="draft", platform_id="linkedin-xxx")
```

## URL handling

LinkedIn has three post URN types. The `lib/url_parser.py` handles all of them:

| URL fragment | URN |
|---|---|
| `/posts/slug-activity-7448...` | `urn:li:activity:7448...` |
| `/posts/slug-share-7449...` | `urn:li:share:7449...` |
| `/feed/update/urn:li:ugcPost:7447...` | `urn:li:ugcPost:7447...` |

Comment URLs include a `commentUrn` query param. The parser extracts both `post_urn` and `comment_id`.

## Thread flattening

LinkedIn flattens reply threads to 2 levels. When replying to a reply, `parentComment` must point to the top-level comment URN, not the reply's URN. The `linkedin-reply-handler` skill handles this correctly.

## Testing the parser

```bash
python lib/url_parser.py "https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20"
```

</details>

## References

- [Publora API docs](https://docs.publora.com) — endpoint reference for the publishing layer
- [Apify console](https://console.apify.com) — manage actors, tokens, and usage for the read layer
- [360Brew paper](https://arxiv.org/abs/2501.16450) — LinkedIn's ranking foundation model
- [AuthoredUp 2026 reach data](https://authoredup.com/) — format-level reach benchmarks

## License

MIT. Powered by [Publora](https://publora.com).

## Related

- [Anthropic Skills repo](https://github.com/anthropics/skills)
- `awesome-claude-skills` directory
