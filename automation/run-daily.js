#!/usr/bin/env node
'use strict';

// Daily LinkedIn comment-candidate workflow. DRAFT-ONLY: this program never publishes, comments,
// reacts, follows or connects. It reads public posts through allowlisted Apify scrapers and writes
// Markdown/JSON files for manual review.

const path = require('path');
const core = require('./lib/core');
const { ApifyReader, ALLOWED_ACTORS } = require('./lib/apify');
const budget = require('./lib/budget');
const { normalizePost, classifyPost, cleanUrl } = require('./lib/filters');
const { scorePost } = require('./lib/score');
const { validateDraft } = require('./lib/validate');
const drafts = require('./lib/drafts');
const render = require('./lib/render');

const HELP = `Usage: node automation/run-daily.js [options]

  (no options)          Live run. Only runs between runWindow hours (IST); exits quietly outside it.
  --force               Ignore the time window.
  --refresh             Run discovery again even if today's list is complete (only new posts are fetched).
  --plan                Show today's budget and discovery plan, make no paid calls, write nothing.
  --no-draft            Skip Claude drafting (candidates only).
  --max-run-usd=0.10    Override budget.maxRunUsd for this run.
  --offline=a.json,b.json [--offline-comments=c.json]
                        Test the pipeline on saved harvestapi datasets. No Apify calls. Writes to
                        automation/output/offline-test and automation/state/offline-test.
  --now=2026-09-15T12:00:00Z
                        Pretend the current time is this (for tests).
`;

function parseArgs(argv) {
  const a = { force: false, refresh: false, plan: false, noDraft: false, offline: null, offlineComments: null, now: null, maxRunUsd: null, help: false };
  for (const arg of argv) {
    if (arg === '--force') a.force = true;
    else if (arg === '--refresh') a.refresh = true;
    else if (arg === '--plan') a.plan = true;
    else if (arg === '--no-draft') a.noDraft = true;
    else if (arg === '--help' || arg === '-h') a.help = true;
    else if (arg.startsWith('--offline=')) a.offline = arg.slice('--offline='.length).split(',').filter(Boolean);
    else if (arg.startsWith('--offline-comments=')) a.offlineComments = arg.slice('--offline-comments='.length);
    else if (arg.startsWith('--now=')) a.now = arg.slice('--now='.length);
    else if (arg.startsWith('--max-run-usd=')) a.maxRunUsd = Number(arg.slice('--max-run-usd='.length));
    else throw new Error(`Unknown argument: ${arg}\n\n${HELP}`);
  }
  if (a.maxRunUsd != null && !(a.maxRunUsd >= 0)) throw new Error('--max-run-usd must be a non-negative number');
  return a;
}

const sum = (xs) => xs.reduce((s, x) => s + (x || 0), 0);
const sameUrl = (a, b) => (cleanUrl(a) || '').replace(/\/$/, '') === (cleanUrl(b) || '').replace(/\/$/, '');

function computeTotals(runs) {
  const live = runs.filter((r) => r.mode === 'live');
  const calls = live.flatMap((r) => r.calls || []);
  return {
    liveRuns: live.length,
    apifyCalls: calls.length,
    estimatedUsd: core.round(sum(calls.map((c) => c.estimatedUsd))),
    actualUsd: core.round(sum(calls.map((c) => c.actualUsd))),
  };
}

function upsertPosts(cache, posts) {
  let added = 0;
  for (const post of posts) {
    const old = cache.posts[post.id];
    if (!old) {
      cache.posts[post.id] = { ...post, firstSeenAt: post.engagementAt };
      added++;
      continue;
    }
    if (Date.parse(post.engagementAt) >= Date.parse(old.engagementAt || 0)) {
      Object.assign(old, { reactions: post.reactions, comments: post.comments, shares: post.shares, engagementAt: post.engagementAt });
    }
    if (post.content.length > (old.content || '').length) old.content = post.content;
    old.sources = [...new Set([...(old.sources || []), ...post.sources])];
  }
  return added;
}

function seedWatchlist(disc, config, nowIso) {
  for (const seed of config.discovery.watchlist.seedProfiles) {
    if (!disc.watchlist[seed.url]) {
      disc.watchlist[seed.url] = { url: seed.url, name: seed.name, source: 'seed', addedAt: nowIso, checks: 0, qualifyingPostIds: [] };
    }
  }
}

function activeWatchlist(disc, config) {
  const entries = Object.values(disc.watchlist).filter((e) => !(e.source === 'learned' && e.checks >= 10 && e.qualifyingPostIds.length === 0));
  const seedRank = (e) => (e.source === 'seed' ? 0 : 1);
  entries.sort((a, b) => b.qualifyingPostIds.length - a.qualifyingPostIds.length || seedRank(a) - seedRank(b));
  return entries.slice(0, config.discovery.watchlist.maxProfiles);
}

function learnAuthors(disc, pool, config, nowIso, log) {
  for (const { post } of pool) {
    const url = post.author.profileUrl;
    if (!url) continue;
    const entry = disc.watchlist[url];
    if (entry) {
      if (!entry.qualifyingPostIds.includes(post.id)) entry.qualifyingPostIds = [...entry.qualifyingPostIds, post.id].slice(-20);
      continue;
    }
    if (!config.discovery.watchlist.learnFromSearch || !post.sources.some((s) => s.startsWith('search:'))) continue;
    const learned = Object.values(disc.watchlist).filter((e) => e.source === 'learned');
    if (Object.keys(disc.watchlist).length >= config.discovery.watchlist.maxProfiles) {
      const evict = learned.sort((a, b) => a.qualifyingPostIds.length - b.qualifyingPostIds.length || b.checks - a.checks)[0];
      if (!evict) continue;
      delete disc.watchlist[evict.url];
      log.info(`Watchlist: removed ${evict.name} to make room`);
    }
    disc.watchlist[url] = { url, name: post.author.name, source: 'learned', addedAt: nowIso, checks: 0, qualifyingPostIds: [post.id] };
    log.info(`Watchlist: added ${post.author.name} (found through search with ${post.reactions} reactions)`);
  }
}

async function discover({ apify, config, disc, cache, fitted, allowance, now, log, run }) {
  const fetchedAt = now.toISOString();
  const maxAgeMs = config.filters.maxAgeHours * 3600000;
  const overlapMs = config.discovery.windowOverlapMinutes * 60000;
  const windowStartMs = disc.lastDiscoveryAt
    ? Math.max(now.getTime() - maxAgeMs, Date.parse(disc.lastDiscoveryAt) - overlapMs)
    : now.getTime() - maxAgeMs;
  const postedLimitDate = new Date(windowStartMs).toISOString();
  const spentSoFar = () => sum(run.calls.map(budget.callCost));
  const capFor = (est) => core.round(Math.min(est * 1.25 + 0.002, Math.max(est, allowance.allowedUsd - spentSoFar())));
  log.info(`Discovery window: posts since ${postedLimitDate}`);
  let ok = 0;

  if (fitted.plan.watchlist.enabled) {
    const profiles = activeWatchlist(disc, config);
    try {
      const items = await apify.runActor(ALLOWED_ACTORS.PROFILE_POSTS, {
        targetUrls: profiles.map((p) => p.url),
        maxPosts: fitted.plan.watchlist.maxPostsPerProfile,
        postedLimitDate,
        includeReposts: false,
        includeQuotePosts: false,
        scrapeReactions: false,
        scrapeComments: false,
      }, { purpose: `watchlist posts (${profiles.length} profiles)`, estimatedUsd: fitted.estimate.watchlist, maxChargeUsd: capFor(fitted.estimate.watchlist), unitPriceUsd: config.budget.pricingUsd.post });
      const added = upsertPosts(cache, items.map((i) => normalizePost(i, 'watchlist', fetchedAt)).filter(Boolean));
      for (const p of profiles) { disc.watchlist[p.url].checks += 1; disc.watchlist[p.url].lastCheckedAt = fetchedAt; }
      log.info(`Watchlist: ${items.length} posts returned, ${added} new`);
      ok++;
    } catch (err) {
      log.error(`Watchlist fetch failed: ${err.message}`);
      run.notes.push(`watchlist fetch failed: ${err.message}`);
    }
  }

  if (fitted.plan.search.enabled) {
    const rotation = config.discovery.search.rotation;
    const queries = Array.from({ length: fitted.plan.search.queries }, (_, i) => rotation[(disc.queryCursor + i) % rotation.length]);
    try {
      const items = await apify.runActor(ALLOWED_ACTORS.POST_SEARCH, {
        searchQueries: queries,
        maxPosts: fitted.plan.search.maxPostsPerQuery,
        postedLimitDate,
        sortBy: config.discovery.search.sortBy,
        scrapeReactions: false,
        scrapeComments: false,
        profileScraperMode: 'short',
      }, { purpose: `keyword search (${queries.join(', ')})`, estimatedUsd: fitted.estimate.search, maxChargeUsd: capFor(fitted.estimate.search), unitPriceUsd: config.budget.pricingUsd.post });
      const posts = items.map((i) => normalizePost(i, `search:${(i.query && i.query.search) || queries.join('|')}`, fetchedAt)).filter(Boolean);
      const added = upsertPosts(cache, posts);
      disc.queryCursor = (disc.queryCursor + queries.length) % rotation.length;
      log.info(`Search: ${items.length} posts returned, ${added} new`);
      ok++;
    } catch (err) {
      log.error(`Keyword search failed: ${err.message}`);
      run.notes.push(`keyword search failed: ${err.message}`);
    }
  }
  return ok > 0;
}

async function fetchExistingComments({ apify, config, shortlist, fitted, allowance, now, log, run }) {
  const refetchMs = config.comments.refetchAfterHours * 3600000;
  const pricing = config.budget.pricingUsd;
  let needs = shortlist.filter((c) => c.post.comments >= config.comments.skipIfCommentCountBelow
    && (!c.post.commentsFetchedAt || now.getTime() - Date.parse(c.post.commentsFetchedAt) > refetchMs));
  if (!needs.length) return;
  const perPost = fitted.plan.comments.maxPerPost;
  const spent = sum(run.calls.map(budget.callCost));
  const left = allowance.allowedUsd - spent - pricing.actorStart;
  const affordable = Math.max(0, Math.min(fitted.plan.comments.posts, Math.floor(left / (perPost * pricing.comment))));
  if (affordable < needs.length) log.warn(`Comments: budget covers ${affordable} of ${needs.length} posts`);
  needs = needs.slice(0, affordable);
  if (!needs.length) { run.notes.push('existing comments not fetched: run budget used up'); return; }
  const est = core.round(needs.length * perPost * pricing.comment + pricing.actorStart);
  try {
    const items = await apify.runActor(ALLOWED_ACTORS.POST_COMMENTS, {
      posts: needs.map((c) => c.post.url),
      maxItems: perPost,
      scrapeReplies: false,
      profileScraperMode: 'short',
    }, { purpose: `existing comments (${needs.length} posts)`, estimatedUsd: est, maxChargeUsd: core.round(Math.max(est, Math.min(est * 1.25 + 0.002, left))), unitPriceUsd: pricing.comment });
    attachComments(needs, items, now);
  } catch (err) {
    log.error(`Comment fetch failed: ${err.message}`);
    run.notes.push(`comment fetch failed: ${err.message}`);
  }
}

function attachComments(candidates, items, now, { onlyMatched = false } = {}) {
  for (const c of candidates) {
    const mine = items.filter((it) => it.query && sameUrl(it.query.post, c.post.url));
    if (onlyMatched && !mine.length) continue;
    c.post.existingComments = mine.map((it) => ({
      author: (it.actor && it.actor.name) || 'unknown',
      headline: String((it.actor && it.actor.position) || '').slice(0, 120),
      text: String(it.commentary || '').slice(0, 400),
    }));
    c.post.commentsFetchedAt = now.toISOString();
  }
}

function candidateRecord(c, rank, config, now) {
  const tz = config.timezone;
  const label = config.timezoneLabel;
  const m = c.model || {};
  return {
    rank,
    postId: c.post.id,
    author: { name: c.post.author.name, headline: c.post.author.headline, profileUrl: c.post.author.profileUrl },
    url: c.post.url,
    postedAt: new Date(c.post.postedAtMs).toISOString(),
    postedAtLocal: core.formatLocal(new Date(c.post.postedAtMs), tz, label),
    ageHours: core.round((now.getTime() - c.post.postedAtMs) / 3600000, 1),
    reactions: c.post.reactions,
    comments: c.post.comments,
    engagementAsOf: c.post.engagementAt,
    engagementAsOfLocal: core.formatLocal(new Date(c.post.engagementAt), tz, label),
    scores: c.scores,
    relevanceScore: c.scores.relevance,
    heuristicRelevance: c.classification.relevance,
    modelRelevance: m.relevance != null ? m.relevance : null,
    reachAssessment: m.reach_assessment || null,
    reason: m.why_worth || null,
    angle: m.angle || null,
    draft: m.draft || null,
    draftChars: m.draft ? [...m.draft].length : 0,
    usesExperience: c.validation ? c.validation.usesExperience : false,
    validation: c.validation || null,
    flags: c.classification.flags,
    matchedTopics: c.classification.matchedTopics,
    injectionSuspected: Boolean(m.injection_suspected),
    existingCommentsReviewed: c.post.existingComments ? c.post.existingComments.length : 0,
    sources: c.post.sources,
  };
}

function applyExperienceQuota(included, config) {
  let uses = 0;
  for (const c of included) {
    if (!c.validation || !c.validation.usesExperience || c.validation.status === 'failed') continue;
    uses++;
    if (uses > config.experience.maxDraftsUsingExperiencePerDay) {
      c.validation.errors.push('experience_quota_exceeded: rewrite without referencing the experience facts');
      c.validation.status = 'failed';
    }
  }
}

async function main(argv, overrides = {}) {
  const args = parseArgs(argv);
  if (args.help) { console.log(HELP); return { status: 'help' }; }

  const config = overrides.config || core.loadConfig();
  const now = args.now ? new Date(args.now) : new Date();
  if (Number.isNaN(now.getTime())) throw new Error(`Invalid --now value: ${args.now}`);
  const mode = args.offline ? 'offline' : 'live';
  const dirs = overrides.dirs || core.defaultDirs(mode);
  const tz = config.timezone;
  const date = core.localDate(now, tz);
  const log = core.createLogger(dirs.logs, date, mode, overrides.quiet);
  const file = {
    usage: path.join(dirs.state, 'usage.json'),
    cache: path.join(dirs.state, 'posts_cache.json'),
    history: path.join(dirs.state, 'history.json'),
    discovery: path.join(dirs.state, 'discovery.json'),
    datedJson: path.join(dirs.output, `daily_candidates_${date}.json`),
    datedMd: path.join(dirs.output, `daily_candidates_${date}.md`),
    latestMd: path.join(dirs.output, 'daily_candidates_latest.md'),
  };

  const usage = core.readJson(file.usage, { version: 1, runs: [] });
  const run = { runId: `${now.toISOString()}#${process.pid}`, date, mode, startedAt: new Date().toISOString(), args: argv, status: 'running', calls: [], claude: { calls: 0, reportedCostUsd: 0 }, notes: [] };
  const finishRun = (status, extra = {}) => {
    Object.assign(run, extra, { status, finishedAt: new Date().toISOString() });
    run.estimatedUsd = core.round(sum(run.calls.map((c) => c.estimatedUsd)));
    run.actualUsd = core.round(sum(run.calls.map((c) => c.actualUsd)));
    run.claude.reportedCostUsd = core.round(run.claude.reportedCostUsd);
    usage.runs = [...(usage.runs || []), run].slice(-200);
    usage.totals = computeTotals(usage.runs);
    usage.updatedAt = new Date().toISOString();
    core.writeJson(file.usage, usage);
  };

  log.info(`Run ${run.runId} (${mode}) for ${date}, local time ${core.formatLocal(now, tz, config.timezoneLabel)}`);

  const hour = core.localHour(now, tz);
  if (mode === 'live' && !args.force && !args.plan && (hour < config.runWindow.startHour || hour >= config.runWindow.endHour)) {
    log.info(`Outside the ${config.runWindow.startHour}:00-${config.runWindow.endHour}:00 ${config.timezoneLabel} window; nothing to do (use --force to override).`);
    finishRun('skipped_outside_window');
    return { status: 'skipped_outside_window' };
  }

  const existing = core.readJson(file.datedJson, null);
  if (existing && existing.status === 'complete' && !args.refresh && !args.plan) {
    core.writeText(file.latestMd, render.renderLatestMarkdown(existing));
    log.info(`Today's list is already complete (${existing.candidates.length} candidates). Re-rendered the latest file; no API calls. Use --refresh to look for newer posts.`);
    finishRun('skipped_existing');
    return { status: 'skipped_existing', report: existing };
  }
  const retryDraftsOnly = Boolean(existing && existing.status === 'drafts_pending' && !args.refresh);

  const releaseLock = args.plan ? () => {} : core.acquireLock(dirs.state, now);
  try {
    const cache = core.readJson(file.cache, { posts: {} });
    const history = core.readJson(file.history, { presented: {}, days: {} });
    const disc = core.readJson(file.discovery, { watchlist: {}, queryCursor: 0, lastDiscoveryAt: null });
    seedWatchlist(disc, config, now.toISOString());
    const pricing = config.budget.pricingUsd;
    const discovery = { ran: false, stopReason: null, steps: [], plan: null, estimate: null, allowance: null };
    let account = null;
    let spentThisCycle = null;
    let apify = null;
    let fitted = null;

    // Stage 1: budget and discovery
    if (mode === 'live') {
      apify = new ApifyReader({ token: core.loadEnv()('APIFY_TOKEN'), runRecord: run, log });
      account = await apify.accountLimits();
      spentThisCycle = budget.automationSpentInCycle(usage, account.cycleStart);
      const allowance = budget.allowedBudget(config, { account, spentThisCycle, maxRunOverride: args.maxRunUsd });
      const firstRun = !disc.lastDiscoveryAt;
      const profiles = activeWatchlist(disc, config);
      const rawPlan = budget.buildPlan(config, { watchlistSize: profiles.length, firstRun, commentFetchSlots: config.selection.shortlistForDrafting });
      const rawEstimate = budget.estimatePlan(rawPlan, pricing);
      fitted = budget.fitPlanToBudget(rawPlan, allowance.allowedUsd, pricing);
      Object.assign(discovery, { plan: fitted.plan, estimate: fitted.estimate, steps: fitted.steps, allowance });
      log.info(`Budget: Apify account $${core.round(account.usedUsd, 3)} of $${account.limitUsd} used this cycle (ends ${account.cycleEnd}); automation spent $${spentThisCycle}; allowed this run $${allowance.allowedUsd} (${allowance.limitedBy}); worst-case plan $${rawEstimate.total} -> $${fitted.estimate.total}${fitted.steps.length ? ` after: ${fitted.steps.join(', ')}` : ''}`);

      if (rawEstimate.total > config.budget.abortIfEstimateOverUsd) {
        discovery.stopReason = `estimated cost $${rawEstimate.total} is above abortIfEstimateOverUsd ($${config.budget.abortIfEstimateOverUsd}); check the discovery settings in automation/config.json`;
      } else if (!fitted.ok) {
        discovery.stopReason = `budget: this run may spend $${allowance.allowedUsd} (${allowance.limitedBy}), not enough for the minimum discovery ($${fitted.estimate.total})`;
      } else if (retryDraftsOnly) {
        discovery.stopReason = 'today\'s discovery already ran; retrying drafts only';
      }

      if (args.plan) {
        const profilesList = profiles.map((p) => `    - ${p.name} (${p.source}, ${p.qualifyingPostIds.length} qualifying posts seen)`).join('\n');
        const rotation = config.discovery.search.rotation;
        const queries = Array.from({ length: fitted.plan.search.queries }, (_, i) => rotation[(disc.queryCursor + i) % rotation.length]);
        console.log([
          `Plan for ${date} (no paid calls made):`,
          `  Apify account: $${core.round(account.usedUsd, 3)} of $${account.limitUsd} used, cycle ${account.cycleStart} -> ${account.cycleEnd}`,
          `  Automation spent this cycle: $${spentThisCycle} of cap $${config.budget.automationCycleCapUsd}`,
          `  Allowed this run: $${allowance.allowedUsd} (${allowance.limitedBy})`,
          `  Worst-case estimate: watchlist $${fitted.estimate.watchlist}, search $${fitted.estimate.search}, comments $${fitted.estimate.comments}, total $${fitted.estimate.total}`,
          `  Adjustments: ${fitted.steps.join(', ') || 'none'}`,
          `  Discovery: ${discovery.stopReason ? `WOULD STOP (${discovery.stopReason})` : 'would run'}`,
          `  Watchlist (${profiles.length}, ${fitted.plan.watchlist.maxPostsPerProfile} posts max each, ${firstRun ? 'first run: last 72h' : `since ${disc.lastDiscoveryAt}`}):`,
          profilesList,
          `  Search queries: ${queries.join(', ') || 'none'}`,
        ].join('\n'));
        return { status: 'plan', plan: fitted, allowance };
      }

      if (discovery.stopReason) {
        log.warn(`Discovery skipped: ${discovery.stopReason}. Continuing with cached posts only.`);
      } else {
        discovery.ran = await discover({ apify, config, disc, cache, fitted, allowance, now, log, run });
        if (discovery.ran) disc.lastDiscoveryAt = now.toISOString();
        else discovery.stopReason = 'all discovery calls failed (see log)';
      }
    } else {
      const items = args.offline.flatMap((f) => core.readJson(path.resolve(f), []));
      const added = upsertPosts(cache, items.map((i) => normalizePost(i, (i.query && i.query.search) ? `search:${i.query.search}` : 'offline', now.toISOString())).filter(Boolean));
      discovery.ran = true;
      log.info(`Offline: loaded ${items.length} items (${added} new posts)`);
    }

    // Stage 2: candidate pool
    const excludedByReason = {};
    const bump = (k) => { excludedByReason[k] = (excludedByReason[k] || 0) + 1; };
    let postsInWindow = 0;
    let qualified = 0;
    const pool = [];
    for (const post of Object.values(cache.posts)) {
      const classification = classifyPost(post, config, now);
      if (!(classification.ageHours >= 0 && classification.ageHours <= config.filters.maxAgeHours)) continue;
      postsInWindow++;
      if (!classification.qualifiesReactions) continue;
      qualified++;
      const presentedOn = history.presented[post.id];
      if (presentedOn && presentedOn !== date && (Date.parse(date) - Date.parse(presentedOn)) / 86400000 <= config.selection.excludePresentedWithinDays) { bump('already_presented_earlier'); continue; }
      if (classification.excluded) { bump(classification.excluded); continue; }
      pool.push({ post, classification });
    }

    const prior = new Map((existing ? existing.candidates : []).map((c) => [c.postId, c]));
    const priorExcluded = new Set((existing ? existing.summary.modelExcluded : []).map((m) => m.postId));
    for (const c of pool) {
      const p = prior.get(c.post.id);
      if (p && p.draft && p.validation && p.validation.status !== 'failed') {
        c.model = { include: true, relevance: p.modelRelevance, insight: p.scores.insight, reach_assessment: p.reachAssessment, why_worth: p.reason, angle: p.angle, draft: p.draft, uses_experience: p.usesExperience, injection_suspected: p.injectionSuspected };
        c.reused = true;
      }
      c.scores = scorePost({ reactions: c.post.reactions, comments: c.post.comments, ageHours: c.classification.ageHours }, { relevance: c.classification.relevance, insight: 50 }, config.weights, config.filters.maxAgeHours);
    }
    pool.sort((a, b) => b.scores.total - a.scores.total);
    const reusedCount = pool.filter((c) => c.reused).length;
    const firstBatch = [
      ...pool.filter((c) => c.reused),
      ...pool.filter((c) => !c.reused && !priorExcluded.has(c.post.id)).slice(0, Math.max(0, config.selection.shortlistForDrafting - reusedCount)),
    ];
    log.info(`Pool: ${postsInWindow} posts in window, ${qualified} with ${config.filters.minReactions}+ reactions, ${pool.length} passed filters, first batch ${firstBatch.length}`);

    // Stages 3-4, per batch: existing comments (so drafts do not repeat them), drafting, validation, one repair pass
    const draftingEnabled = config.draft.enabled && !args.noDraft;
    let status = 'complete';
    let rules = null;
    const shortlist = [];
    const included = () => shortlist.filter((c) => c.model && c.model.include).sort((a, b) => b.scores.total - a.scores.total);
    const usable = () => included().filter((c) => c.validation && c.validation.status !== 'failed');
    const validateAll = () => {
      for (const c of included()) c.validation = validateDraft(c.model.draft, config.draft);
      applyExperienceQuota(included(), config);
    };

    const processBatch = async (batch) => {
      shortlist.push(...batch);
      const fresh = batch.filter((c) => !c.reused);
      if (mode === 'live' && discovery.ran && fitted && fitted.plan.comments.enabled) {
        await fetchExistingComments({ apify, config, shortlist: fresh, fitted, allowance: discovery.allowance, now, log, run });
      } else if (mode === 'offline' && args.offlineComments) {
        attachComments(fresh.filter((c) => c.post.comments > 0), core.readJson(path.resolve(args.offlineComments), []), now, { onlyMatched: true });
      }
      if (!draftingEnabled || status !== 'complete') return;
      if (!fresh.length) { validateAll(); return; }

      rules = rules || drafts.loadRules(log);
      const experienceUsesLeft = Math.max(0, config.experience.maxDraftsUsingExperiencePerDay - usable().filter((c) => c.validation.usesExperience).length);
      try {
        log.info(`Drafting ${fresh.length} candidates with Claude Code (no tools)`);
        const res = await drafts.runClaude(drafts.buildDraftPrompt(fresh, config, rules, { experienceUsesLeft }), drafts.DRAFT_SCHEMA, config, log);
        run.claude.calls++;
        run.claude.reportedCostUsd += res.costUsd;
        const byId = new Map(res.data.candidates.map((x) => [String(x.id), x]));
        for (const c of fresh) c.model = byId.get(c.post.id) || null;
        const missing = fresh.filter((c) => !c.model).length;
        if (missing) log.warn(`Claude returned no result for ${missing} candidates`);
      } catch (err) {
        log.error(`Drafting failed: ${err.message}`);
        run.notes.push(`drafting failed: ${err.message}`);
        status = 'drafts_pending';
        return;
      }

      validateAll();
      const failures = included().filter((c) => fresh.includes(c) && c.validation.status === 'failed');
      if (!failures.length || !config.draft.repairInvalidOnce) return;
      log.info(`Repairing ${failures.length} drafts that failed checks`);
      try {
        const prompt = drafts.buildRepairPrompt(failures.map((c) => ({ candidate: c, draft: c.model.draft, angle: c.model.angle, errors: c.validation.errors })), config, rules);
        const res = await drafts.runClaude(prompt, drafts.REPAIR_SCHEMA, config, log);
        run.claude.calls++;
        run.claude.reportedCostUsd += res.costUsd;
        const byId = new Map(res.data.candidates.map((x) => [String(x.id), x]));
        for (const c of failures) {
          const fixed = byId.get(c.post.id);
          if (fixed) { c.model.draft = fixed.draft; c.model.uses_experience = fixed.uses_experience; }
        }
        validateAll();
      } catch (err) {
        log.error(`Repair pass failed: ${err.message}`);
        run.notes.push(`repair failed: ${err.message}`);
      }
    };

    await processBatch(firstBatch);
    for (let round = 1; round <= config.selection.topUpRounds && draftingEnabled && status === 'complete'; round++) {
      const have = usable().length;
      if (have >= config.selection.finalCount) break;
      const remaining = pool.filter((c) => !shortlist.includes(c) && !priorExcluded.has(c.post.id));
      if (!remaining.length) break;
      const batch = remaining.slice(0, config.selection.finalCount - have + 2);
      log.info(`Top-up round ${round}: ${have} usable drafts, drafting ${batch.length} more candidates`);
      await processBatch(batch);
    }

    // Stage 5: final scoring and selection
    const modelExcluded = [];
    const validationDropped = [];
    const scored = [];
    for (const c of shortlist) {
      if (c.model && !c.model.include) {
        modelExcluded.push({ postId: c.post.id, author: c.post.author.name, url: c.post.url, reason: c.model.exclude_reason || 'not relevant enough' });
        continue;
      }
      const relevance = c.model && c.model.relevance != null ? Math.round(0.3 * c.classification.relevance + 0.7 * c.model.relevance) : c.classification.relevance;
      const insight = c.model && c.model.insight != null ? c.model.insight : 50;
      c.scores = scorePost({ reactions: c.post.reactions, comments: c.post.comments, ageHours: c.classification.ageHours }, { relevance, insight }, config.weights, config.filters.maxAgeHours);
      if (draftingEnabled && status === 'complete') {
        if (!c.model) continue;
        if (!c.validation || c.validation.status === 'failed') {
          validationDropped.push({ postId: c.post.id, author: c.post.author.name, errors: c.validation ? c.validation.errors : ['no draft returned'] });
          continue;
        }
      }
      scored.push(c);
    }
    scored.sort((a, b) => b.scores.total - a.scores.total);
    const final = scored.slice(0, config.selection.finalCount);

    let shortfall = null;
    if (final.length < config.selection.finalCount) {
      shortfall = `Only ${qualified} posts from the last ${config.filters.maxAgeHours}h had ${config.filters.minReactions}+ reactions (threshold not lowered); ${pool.length} passed the filters and ${final.length} made the final list.`;
      if (discovery.stopReason) shortfall += ` Discovery did not run: ${discovery.stopReason}.`;
    }

    const report = {
      schemaVersion: 1,
      date,
      generatedAt: new Date().toISOString(),
      generatedAtLocal: core.formatLocal(new Date(), tz, config.timezoneLabel),
      timezone: tz,
      mode,
      status,
      draftsEnabled: draftingEnabled,
      thresholds: { minReactions: config.filters.minReactions, maxAgeHours: config.filters.maxAgeHours },
      weights: config.weights,
      summary: {
        postsInWindow, qualifiedByReactions: qualified, passedFilters: pool.length, shortlisted: shortlist.length,
        drafted: shortlist.filter((c) => c.model && c.model.draft).length, final: final.length,
        excludedByReason, modelExcluded, validationDropped, shortfall,
      },
      discovery: { ran: discovery.ran, stopReason: discovery.stopReason, steps: discovery.steps, estimateUsd: discovery.estimate, allowance: discovery.allowance },
      cost: {
        runEstimatedUsd: core.round(sum(run.calls.map((c) => c.estimatedUsd))),
        runActualUsd: core.round(sum(run.calls.map((c) => c.actualUsd))),
        apifyCalls: run.calls.length,
        automationSpentThisCycleUsd: spentThisCycle == null ? null : core.round(spentThisCycle + sum(run.calls.map((c) => c.actualUsd))),
        accountUsedUsd: account ? core.round(account.usedUsd + sum(run.calls.map((c) => c.actualUsd))) : null,
        accountLimitUsd: account ? account.limitUsd : null,
        cycleEnd: account ? account.cycleEnd : null,
        claudeCalls: run.claude.calls,
        claudeReportedCostUsd: core.round(run.claude.reportedCostUsd),
      },
      notes: run.notes,
      candidates: final.map((c, i) => candidateRecord(c, i + 1, config, now)),
    };

    core.writeJson(file.datedJson, report);
    core.writeText(file.datedMd, render.renderDatedMarkdown(report));
    core.writeText(file.latestMd, render.renderLatestMarkdown(report));

    if (status === 'complete') {
      history.days[date] = report.candidates.map((c) => c.postId);
      for (const c of report.candidates) history.presented[c.postId] = history.presented[c.postId] || date;
    }
    if (mode === 'live') learnAuthors(disc, pool, config, now.toISOString(), log);
    const retainMs = config.cache.retainDays * 86400000;
    for (const [id, p] of Object.entries(cache.posts)) if (!p.postedAtMs || now.getTime() - p.postedAtMs > retainMs) delete cache.posts[id];
    core.writeJson(file.cache, cache);
    core.writeJson(file.history, history);
    core.writeJson(file.discovery, disc);

    log.info(`Done: ${status}, ${final.length} candidates -> ${file.latestMd}`);
    log.info(`Apify this run: estimated $${report.cost.runEstimatedUsd}, charged $${report.cost.runActualUsd}; Claude calls ${run.claude.calls}`);
    finishRun(status, { summary: { final: final.length, qualified, passedFilters: pool.length } });
    return { status, report };
  } catch (err) {
    log.error(err.stack || err.message);
    finishRun('failed', { error: err.message });
    throw err;
  } finally {
    releaseLock();
  }
}

if (require.main === module) {
  main(process.argv.slice(2)).then(
    (res) => { process.exitCode = res.status === 'failed' ? 1 : 0; },
    (err) => { console.error(err.code === 'LOCKED' ? err.message : `Run failed: ${err.message}`); process.exitCode = 1; },
  );
}

module.exports = { main, parseArgs };
