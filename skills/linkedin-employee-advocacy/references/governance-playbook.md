# Governance Playbook — What to review, what not to, SLA

The fastest way to kill an advocacy program is a 24-hour review queue. The fastest way to embarrass the company is no review at all. This playbook is the middle path.

## Core principle: review the risk surface, trust the voice surface

Every post has two things in it:

- **Risk surface:** specific claims, customer names, product roadmap commitments, regulated-industry guidance, financial figures, competitor mentions.
- **Voice surface:** opinion, narrative, hook style, sentence rhythm, emoji usage, vulnerability.

Review the risk surface. Never review the voice surface. If you correct someone's voice, they stop posting; the program dies in 6 weeks.

## The 3-tier review queue

### Tier A — No review (auto-publish)

- Comments on third-party posts
- Reposts with a 1-2 sentence personal angle
- Posts where the team member is sharing a personal lesson, story, or opinion with no claims about specific customers, financials, roadmap, or competitors
- Polls, except when the answers would constitute roadmap or pricing signal

**Estimated coverage:** 70-80% of advocacy content.

### Tier B — Voice-capture review (24h SLA, async)

- Posts that name a customer (even publicly-known one)
- Posts that reference a specific number from internal data (revenue, retention, churn, ARR, conversion rate)
- Posts that critique a named competitor
- Posts that announce something we haven't announced yet

**Reviewer:** a marketing IC with brand authority (not a manager). One reviewer per 5-10 advocates.
**Action:** check the named entity is OK to mention publicly, check the number is releasable, check the timing. Almost never edit voice.

**Estimated coverage:** 15-25% of advocacy content.

### Tier C — Legal / exec review (48h SLA)

- Posts about a regulated topic (HIPAA, SOX, GDPR, CCPA, securities, medical claims)
- Posts that could be read as forward-looking statements (revenue guidance, M&A, fundraising)
- Posts about an ongoing dispute, lawsuit, or PR incident
- Posts that name a customer where contractual confidentiality is a question

**Reviewer:** General Counsel + at least one C-level (depending on topic).

**Estimated coverage:** <5% of advocacy content.

## SLA commitments

| Tier | SLA target | What "miss" means |
|---|---|---|
| A | 0 minutes (auto) | n/a |
| B | 24 business hours | Author can publish if no response by hour 24 (silent-approval rule) |
| C | 48 business hours | Author must wait for explicit go/no-go |

Silent approval at Tier B is what makes the program survive. If you can't commit to 24h, you can't run an advocacy program; pick a longer SLA and accept the lower volume.

## What reviewers must NEVER edit

- Lowercase sentence starts (signature voice)
- `..` as soft pause
- Sentence fragments
- First-person stakes / vulnerability
- The hook (rewriting the hook = rewriting the post)
- Specific numbers that the author personally witnessed (vs internal-only metrics)
- Cadence (timing is the author's call)

If a reviewer does any of this, the author's next 3 posts will be sanitized corporate boilerplate, and they'll quietly stop after 4 weeks.

## What reviewers MUST flag

- Customer name without confirmed permission
- Specific revenue / retention / churn figures from internal dashboards
- Product capability claims that aren't currently shipped
- Financial guidance, even directional ("we're growing fast" implies growth → potentially material)
- Specific competitor allegations (factual or not)
- Any mention of a current employee by name without their consent
- Anything that mentions an ongoing legal matter

## Reviewer scorecard

Track these per reviewer to keep the program healthy:

| Metric | Healthy | Warning |
|---|---|---|
| Tier-B SLA hit rate | >90% | <75% |
| Tier-B edits per post | <0.5 | >2 |
| Voice-rule violations introduced by reviewer | 0 | any |
| Author-reported review-friction (quarterly survey) | <2/10 | >4/10 |

Reviewer who scores Warning on any line gets coached or rotated.

## Rolling 30-day audit

Once a month, sample 10% of Tier-A (auto-publish) posts and verify they were genuinely Tier A. Look for:

- Customer names that should have been Tier B
- Specific numbers that should have been Tier B
- Competitor mentions that should have been Tier B

If audit reveals more than 2 misclassifications per 100 sampled, tighten the Tier-A definition. If it reveals fewer than 1 per 1,000, loosen it (you're over-reviewing).

## Bypass for incidents

In an active PR / outage incident, all Tier-A auto-publish is suspended for 5-7 days for the affected team. Communications routes through the designated incident-comms voice only. Resume Tier A once the incident-comms team gives the all-clear.

## Tooling expectations (not requirements)

- A queue tool (Slack channel, Notion DB, dedicated platform) where Tier-B drafts land with reviewer assignment
- A keyword pre-filter that auto-tags drafts as B/C based on customer-name list, competitor list, regulated-keyword list
- An audit log of every Tier-B/C decision with reviewer + timestamp

The program can run on a Slack channel + spreadsheet. It does not need a dedicated SaaS.
