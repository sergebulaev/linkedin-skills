'use strict';

const { round } = require('./core');

function buildPlan(config, { watchlistSize, firstRun, commentFetchSlots }) {
  const d = config.discovery;
  return {
    watchlist: {
      enabled: d.watchlist.enabled && watchlistSize > 0,
      profiles: watchlistSize,
      maxPostsPerProfile: firstRun ? d.watchlist.maxPostsPerProfileFirstRun : d.watchlist.maxPostsPerProfile,
    },
    search: {
      enabled: d.search.enabled && d.search.queriesPerRun > 0,
      queries: d.search.queriesPerRun,
      maxPostsPerQuery: d.search.maxPostsPerQuery,
    },
    comments: {
      enabled: commentFetchSlots > 0,
      posts: commentFetchSlots,
      maxPerPost: config.comments.maxPerPost,
    },
  };
}

// Worst case: every profile/query returns its maximum, every shortlisted post returns maxPerPost comments.
function estimatePlan(plan, pricing) {
  const w = plan.watchlist.enabled
    ? plan.watchlist.profiles * plan.watchlist.maxPostsPerProfile * pricing.post + pricing.actorStart
    : 0;
  const s = plan.search.enabled
    ? plan.search.queries * Math.max(plan.search.maxPostsPerQuery * pricing.post, pricing.noResult) + pricing.actorStart
    : 0;
  const c = plan.comments.enabled
    ? plan.comments.posts * plan.comments.maxPerPost * pricing.comment + pricing.actorStart
    : 0;
  return { watchlist: round(w), search: round(s), comments: round(c), total: round(w + s + c) };
}

// Shrinks the optional parts of the plan until it fits. Watchlist posts are the core source, so they go last.
function fitPlanToBudget(plan, allowedUsd, pricing) {
  const p = JSON.parse(JSON.stringify(plan));
  const steps = [];
  const fits = () => estimatePlan(p, pricing).total <= allowedUsd + 1e-9;

  const shrinkers = [
    () => { if (p.search.enabled && p.search.queries > 0) { p.search.enabled = false; p.search.queries = 0; return 'dropped keyword search'; } },
    () => { if (p.comments.enabled && p.comments.maxPerPost > 2) { p.comments.maxPerPost = 2; return 'comments per post -> 2'; } },
    () => { if (p.comments.enabled && p.comments.posts > 6) { p.comments.posts = 6; return 'comment fetches -> 6 posts'; } },
    () => { if (p.watchlist.enabled && p.watchlist.maxPostsPerProfile > 1) { p.watchlist.maxPostsPerProfile = 1; return 'watchlist posts per profile -> 1'; } },
    () => { if (p.comments.enabled) { p.comments.enabled = false; p.comments.posts = 0; return 'dropped comment fetches'; } },
  ];
  for (const shrink of shrinkers) {
    if (fits()) break;
    const step = shrink();
    if (step) steps.push(step);
  }
  const estimate = estimatePlan(p, pricing);
  const hasDiscovery = p.watchlist.enabled || p.search.enabled;
  return { plan: p, estimate, steps, ok: fits() && hasDiscovery };
}

// Conservative cost of one recorded call: an unsettled charge counts at its worst-case estimate.
function callCost(call) {
  const actual = call.actualUsd || 0;
  return call.settled === true ? actual : Math.max(actual, call.estimatedUsd || 0);
}

function automationSpentInCycle(usage, cycleStartIso) {
  const since = cycleStartIso ? Date.parse(cycleStartIso) : 0;
  let total = 0;
  for (const run of usage.runs || []) {
    if (run.mode !== 'live' || Date.parse(run.startedAt) < since) continue;
    for (const call of run.calls || []) total += callCost(call);
  }
  return round(total);
}

function allowedBudget(config, { account, spentThisCycle, maxRunOverride }) {
  const b = config.budget;
  const perRun = maxRunOverride != null ? maxRunOverride : b.maxRunUsd;
  const automationLeft = b.automationCycleCapUsd - spentThisCycle;
  const accountLeft = account.limitUsd - account.usedUsd - b.accountReserveUsd;
  const allowed = Math.max(0, Math.min(perRun, automationLeft, accountLeft));
  let limitedBy = 'maxRunUsd';
  if (allowed === automationLeft) limitedBy = 'automationCycleCapUsd';
  if (allowed === accountLeft) limitedBy = 'accountReserveUsd (Apify account nearly used up)';
  if (allowed === 0) limitedBy = accountLeft <= automationLeft ? 'Apify account allowance minus reserve is exhausted' : 'automation cycle cap is exhausted';
  return { allowedUsd: round(allowed), perRun, automationLeft: round(automationLeft), accountLeft: round(accountLeft), limitedBy };
}

module.exports = { buildPlan, estimatePlan, fitPlanToBudget, automationSpentInCycle, allowedBudget, callCost };
