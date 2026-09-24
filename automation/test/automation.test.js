'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const core = require('../lib/core');
const { normalizePost, classifyPost } = require('../lib/filters');
const { scorePost, competitionScore } = require('../lib/score');
const { validateDraft } = require('../lib/validate');
const budget = require('../lib/budget');
const { ApifyReader } = require('../lib/apify');
const drafts = require('../lib/drafts');
const { main } = require('../run-daily');

const config = core.loadConfig();
const NOW = new Date('2026-09-15T12:00:00Z'); // 17:30 IST

function activityId(ms, salt) {
  return ((BigInt(ms) << 22n) | BigInt(salt)).toString();
}

function item({ salt, content, likes = 250, comments = 30, hoursAgo = 10, authorType = 'profile', job = null, header = null, name = 'Test Author' }) {
  const ms = NOW.getTime() - hoursAgo * 3600000;
  const id = activityId(ms, salt);
  return {
    type: 'post',
    id,
    linkedinUrl: `https://www.linkedin.com/posts/test-author_topic-activity-${id}-abcd`,
    content,
    author: { name, publicIdentifier: `author-${salt}`, type: authorType, info: 'Engineer' },
    postedAt: { timestamp: ms },
    engagement: { likes, comments, shares: 1 },
    job,
    header,
    query: { search: 'system design' },
  };
}

const TECH = 'Scaling a Node.js API: we moved heavy JSON parsing to streams with backpressure, added Redis caching, and fixed database connection pool exhaustion under high traffic. Latency p99 dropped once the event loop stopped blocking.';

function classify(i) {
  return classifyPost(normalizePost(i, 'test', NOW.toISOString()), config, NOW);
}

test('filters keep a relevant technical post and exclude jobs, groups, companies, promos, giveaways, fluff', () => {
  assert.equal(classify(item({ salt: 1, content: TECH })).excluded, null);
  assert.equal(classify(item({ salt: 2, content: TECH, job: { title: 'Backend Engineer' } })).excluded, 'job_post');
  assert.equal(classify(item({ salt: 3, content: `We're hiring a Node.js backend developer. ${TECH}` })).excluded, 'job_post');
  assert.equal(classify(item({ salt: 4, content: TECH, header: { text: 'New post in Java Developers' } })).excluded, 'group_post');
  assert.equal(classify(item({ salt: 5, content: TECH, authorType: 'company' })).excluded, 'company_page');
  assert.equal(classify(item({ salt: 6, content: `Introducing our new API monitoring tool! Start your free trial today. ${TECH}` })).excluded, 'product_promotion');
  assert.equal(classify(item({ salt: 7, content: `Comment "SYSTEM" below and I'll send you my system design notes. ${TECH}` })).excluded, 'comment_gate_giveaway');
  assert.equal(classify(item({ salt: 8, content: 'Grateful for my journey. Never give up, keep going and believe in yourself. My mindset changed everything this year.' })).excluded, 'unrelated_to_positioning');
  assert.equal(classify(item({ salt: 9, content: 'Happy Monday everyone, enjoy the sunshine and a great coffee with your team today.' })).excluded, 'unrelated_to_positioning');
  assert.equal(classify(item({ salt: 10, content: TECH, hoursAgo: 80 })).excluded, 'too_old');
  const psPlug = `${TECH} Retries, timeouts and failovers are essential in every design.\n\nP.S. Preparing for interviews? Check out my book, available on Amazon. Join my newsletter too.`;
  assert.equal(classify(item({ salt: 13, content: psPlug })).excluded, null, 'a P.S. plug must not make a technical post a promotion');
  assert.equal(classify(item({ salt: 14, content: `My SaaS is live now! Try it for free and sign up today. ${TECH}` })).excluded, 'product_promotion');
  const deep = 'Tip: Claude Code has cleanup commands. Every skill in the listing costs tokens, and CLAUDE.md debt piles up. The plugin manager shows what each one costs so you can cut dead weight from the context window.';
  assert.equal(classify(item({ salt: 15, content: deep })).excluded, null, 'a post deep in one topic must not be marked unrelated');
  const low = classify(item({ salt: 11, content: TECH, likes: 40 }));
  assert.equal(low.qualifiesReactions, false);
  assert.equal(classify(item({ salt: 12, content: TECH })).experienceMatch, true);
});

test('ranking favours visibility of a new comment over raw reaction count', () => {
  const rel = { relevance: 80, insight: 60 };
  const modest = scorePost({ reactions: 300, comments: 30, ageHours: 24 }, rel, config.weights, 72);
  const crowded = scorePost({ reactions: 2000, comments: 2000, ageHours: 24 }, rel, config.weights, 72);
  assert.ok(modest.total > crowded.total, `expected 300/30 (${modest.total}) to beat 2000/2000 (${crowded.total})`);
  assert.equal(competitionScore(0, 300), 25);
  assert.equal(competitionScore(20, 300), 100);
  const fresh = scorePost({ reactions: 300, comments: 30, ageHours: 2 }, rel, config.weights, 72);
  assert.ok(fresh.total > modest.total);
});

test('draft validation enforces comment rules and blocks invented experience', () => {
  const opts = config.draft;
  const ok = 'Neo, I would add bulk ingestion to the list. A single ~700MB JSON file with 100K+ records in Node.js already forces streaming, batching and backpressure decisions, the same trade-offs these systems make at larger scale.';
  assert.equal(validateDraft(ok, opts).status !== 'failed', true, JSON.stringify(validateDraft(ok, opts)));
  assert.equal(validateDraft(ok, opts).usesExperience, true);

  const general = 'Shalini, a concrete case for myth one: every app server you add brings its own connection pool, and the database limit does not move. Ten instances with a pool of 20 can ask Postgres for 200 connections against a default max_connections of 100.';
  assert.notEqual(validateDraft(general, opts).status, 'failed');

  const fails = (text, code) => {
    const v = validateDraft(text, opts);
    assert.equal(v.status, 'failed', `${code} not caught: ${text}`);
    assert.ok(v.errors.some((e) => e.startsWith(code)), `expected ${code}, got ${v.errors.join(' | ')}`);
  };
  const pad = ' The failure mode shows up when a consumer falls behind and the queue keeps growing without any limit applied upstream.';
  fails(`Great post! Idempotency keys matter for retries.${pad}`, 'generic_praise');
  fails(`Idempotency keys protect retries on POST endpoints #backend${pad}`, 'hashtag');
  fails(`Idempotency keys protect retries on POST endpoints \u{1F680}${pad}`, 'emoji');
  fails(`At my company we reduced p99 latency by 40% after moving to keyset pagination.${pad}`, 'possible_invented_experience');
  fails(`I migrated our Kafka consumers to idempotent writes last year and duplicates stopped.${pad}`, 'possible_invented_experience');
  fails(`I processed a ~700MB JSON file with 100K+ records in Node.js and cut runtime by 80%.${pad}`, 'experience_detail_not_provided');
  fails(`Even streaming ~700MB of JSON with 100K+ records in a single Node.js process, I paired batching with backpressure.${pad}`, 'experience_detail_not_provided');
  fails(`Retries without idempotency keys create duplicate orders. Agree?${pad}`, 'engagement_bait');
  fails(`It's not about caching, it's about invalidation.${pad}`, 'ai_phrasing_pattern');
  fails(`Check the docs at https://example.com for the details.${pad}`, 'link');
  fails('Too short to be useful.', 'too_short');
});

test('budget planner shrinks optional work first and refuses when discovery cannot fit', () => {
  const pricing = config.budget.pricingUsd;
  const plan = budget.buildPlan(config, { watchlistSize: 11, firstRun: false, commentFetchSlots: 12 });
  const full = budget.estimatePlan(plan, pricing);
  assert.ok(full.total > 0.1);

  const fitted = budget.fitPlanToBudget(plan, full.total - 0.01, pricing);
  assert.equal(fitted.ok, true);
  assert.equal(fitted.plan.search.enabled, false);
  assert.ok(fitted.estimate.total <= full.total - 0.01);

  const broke = budget.fitPlanToBudget(plan, 0.005, pricing);
  assert.equal(broke.ok, false);

  const usage = { runs: [
    { mode: 'live', startedAt: '2026-09-16T12:00:00Z', calls: [{ estimatedUsd: 0.1, actualUsd: 0.07 }] },
    { mode: 'live', startedAt: '2026-09-01T12:00:00Z', calls: [{ estimatedUsd: 0.1, actualUsd: 0.09 }] },
    { mode: 'offline', startedAt: '2026-09-16T12:00:00Z', calls: [{ estimatedUsd: 0.5, actualUsd: 0.5 }] },
  ] };
  assert.equal(budget.automationSpentInCycle(usage, '2026-09-15T00:00:00Z'), 0.1, 'unsettled calls count at their estimate');
  usage.runs[0].calls[0].settled = true;
  assert.equal(budget.automationSpentInCycle(usage, '2026-09-15T00:00:00Z'), 0.07);
  assert.equal(budget.callCost({ estimatedUsd: 0.072, actualUsd: 0, settled: false }), 0.072);

  const allowance = budget.allowedBudget(config, { account: { usedUsd: 4.8, limitUsd: 5 }, spentThisCycle: 0 });
  assert.equal(allowance.allowedUsd, 0);
});

test('safety: the daily discovery/drafting pipeline has zero publishing code paths', async () => {
  // lib/publora.js is the one file whose entire job is calling Publora's comment endpoint, used
  // only by publish-cli.js's "publish" command. Every other file, and above all run-daily.js (the
  // unattended, scheduled pipeline), must contain no trace of a publish/reaction/reshare endpoint.
  const forbidden = [/publora_client/i, /publora\.com/i, /PUBLORA_API_KEY/, /linkedin-comments/i, /linkedin-reactions/i, /linkedin-reshare/i, /create-post/i, /post_comment\.py/i, /schedule_post\.py/i, /lib\.publish/i, /\brepost\(/i];
  const dir = path.join(__dirname, '..');
  const libFiles = fs.readdirSync(path.join(dir, 'lib')).map((f) => path.join('lib', f)).filter((f) => f !== path.join('lib', 'publora.js'));
  const files = ['run-daily.js', 'run-daily.cmd', ...libFiles];
  for (const f of files) {
    const src = fs.readFileSync(path.join(dir, f), 'utf8');
    for (const re of forbidden) assert.ok(!re.test(src), `${f} contains forbidden pattern ${re}`);
  }

  // Structural check: the scheduled pipeline must not even import the modules that can publish.
  const runDailySrc = fs.readFileSync(path.join(dir, 'run-daily.js'), 'utf8');
  assert.ok(!/require\(['"].\/lib\/publora['"]\)/.test(runDailySrc), 'run-daily.js must not import lib/publora.js');
  assert.ok(!/require\(['"].\/lib\/queue['"]\)/.test(runDailySrc), 'run-daily.js must not import lib/queue.js (publishing is a separate, explicit step)');

  const reader = new ApifyReader({ token: 'test', runRecord: { calls: [] }, log: { info() {}, warn() {}, error() {} }, fetchImpl: () => { throw new Error('network must not be touched'); } });
  await assert.rejects(reader.runActor('apimaestro~linkedin-post-detail', {}, { purpose: 'x', estimatedUsd: 0.01, maxChargeUsd: 0.01 }), /non-allowlisted/);
  await assert.rejects(reader.runActor('harvestapi~linkedin-post-search', {}, { purpose: 'x', estimatedUsd: 0.01, maxChargeUsd: 0 }), /maxChargeUsd/);
});

test('drafting prompt reuses every repository rule section it expects', () => {
  const warnings = [];
  const rules = drafts.loadRules({ warn: (m) => warnings.push(m), info() {} });
  assert.deepEqual(warnings, []);
  assert.match(rules, /Hard rules/);
  assert.match(rules, /Non-negotiable rules/);
  assert.match(rules, /data, never an instruction|data only|data\. It is never/i);
  assert.equal(drafts.extractSection('# A\n```\n# not a heading\n```\ntext\n# B\n', 'A'), '# A\n```\n# not a heading\n```\ntext');
});

test('offline run is idempotent within a day and does not re-propose posts the next day', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'li-automation-test-'));
  const dirs = { output: path.join(tmp, 'output'), state: path.join(tmp, 'state'), logs: path.join(tmp, 'logs') };
  const fixture = path.join(tmp, 'posts.json');
  const items = Array.from({ length: 14 }, (_, i) => item({ salt: 100 + i, content: `${TECH} Case ${i}.`, likes: 120 + i * 40, comments: 5 + i, hoursAgo: 2 + i, name: `Author ${i}` }));
  items.push(item({ salt: 200, content: TECH, job: { title: 'x' } }));
  items.push(item({ salt: 201, content: TECH, likes: 50 }));
  fs.writeFileSync(fixture, JSON.stringify(items));

  const args = [`--offline=${fixture}`, '--no-draft', `--now=${NOW.toISOString()}`];
  const first = await main(args, { dirs, quiet: true });
  assert.equal(first.status, 'complete');
  assert.equal(first.report.candidates.length, 10);
  assert.equal(first.report.summary.qualifiedByReactions, 15);
  assert.equal(first.report.summary.excludedByReason.job_post, 1);
  const ids = new Set(first.report.candidates.map((c) => c.postId));
  assert.equal(ids.size, 10);
  for (const name of ['daily_candidates_2026-09-15.json', 'daily_candidates_2026-09-15.md', 'daily_candidates_latest.md']) {
    assert.ok(fs.existsSync(path.join(dirs.output, name)), `${name} missing`);
  }

  const second = await main(args, { dirs, quiet: true });
  assert.equal(second.status, 'skipped_existing');
  const usage = core.readJson(path.join(dirs.state, 'usage.json'), null);
  assert.equal(usage.runs.length, 2);
  assert.equal(usage.runs.flatMap((r) => r.calls).length, 0);

  const nextDay = new Date(NOW.getTime() + 24 * 3600000);
  const third = await main([`--offline=${fixture}`, '--no-draft', `--now=${nextDay.toISOString()}`], { dirs, quiet: true });
  const again = third.report.candidates.filter((c) => ids.has(c.postId));
  assert.equal(again.length, 0, 'posts presented yesterday must not be proposed again');
  assert.equal(third.report.summary.excludedByReason.already_presented_earlier, 10);

  fs.rmSync(tmp, { recursive: true, force: true });
});

test('live run outside the 17:00-20:00 IST window exits before any API call', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'li-automation-window-'));
  const dirs = { output: path.join(tmp, 'output'), state: path.join(tmp, 'state'), logs: path.join(tmp, 'logs') };
  const res = await main(['--now=2026-09-15T04:30:00Z'], { dirs, quiet: true });
  assert.equal(res.status, 'skipped_outside_window');
  fs.rmSync(tmp, { recursive: true, force: true });
});
