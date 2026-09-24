'use strict';

const { round } = require('./core');

const BASE_URL = 'https://api.apify.com/v2';

// Read-only scrapers. Anything else (in particular anything that writes to LinkedIn) is refused.
const ALLOWED_ACTORS = Object.freeze({
  PROFILE_POSTS: 'harvestapi~linkedin-profile-posts',
  POST_SEARCH: 'harvestapi~linkedin-post-search',
  POST_COMMENTS: 'harvestapi~linkedin-post-comments',
  PROFILE_DETAILS: 'harvestapi~linkedin-profile-scraper',
});
const ALLOWED_SET = new Set(Object.values(ALLOWED_ACTORS));

const TERMINAL = new Set(['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class ApifyReader {
  // onCallUpdate runs after every call is recorded and again when it ends (success or failure), so the
  // spend ledger survives a run that is killed before it finishes.
  constructor({ token, runRecord, log, fetchImpl = fetch, onCallUpdate = () => {} }) {
    if (!token) throw new Error('APIFY_TOKEN is not set (checked environment and repo-root .env).');
    this.token = token;
    this.runRecord = runRecord;
    this.log = log;
    this.fetch = fetchImpl;
    this.onCallUpdate = onCallUpdate;
  }

  async request(method, pathAndQuery, body) {
    let lastErr;
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const res = await this.fetch(`${BASE_URL}${pathAndQuery}`, {
          method,
          headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' },
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: AbortSignal.timeout(120000),
        });
        const text = await res.text();
        if (res.status === 429 || res.status >= 500) throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
        if (res.status >= 400) throw Object.assign(new Error(`HTTP ${res.status}: ${text.slice(0, 300)}`), { fatal: true });
        return text ? JSON.parse(text) : null;
      } catch (err) {
        lastErr = err;
        if (err.fatal || attempt === 3) break;
        await sleep(2000 * attempt);
      }
    }
    throw lastErr;
  }

  async accountLimits() {
    const data = (await this.request('GET', '/users/me/limits')).data || {};
    return {
      cycleStart: data.monthlyUsageCycle && data.monthlyUsageCycle.startAt,
      cycleEnd: data.monthlyUsageCycle && data.monthlyUsageCycle.endAt,
      usedUsd: (data.current && data.current.monthlyUsageUsd) || 0,
      limitUsd: (data.limits && data.limits.maxMonthlyUsageUsd) || 0,
    };
  }

  // unitPriceUsd: price per returned item, used as a floor while Apify's own charge accounting settles.
  async runActor(actorId, input, { purpose, estimatedUsd, maxChargeUsd, unitPriceUsd = 0, timeoutMs = 10 * 60 * 1000 }) {
    if (!ALLOWED_SET.has(actorId)) throw new Error(`Refusing to run non-allowlisted actor "${actorId}"`);
    if (!(maxChargeUsd > 0)) throw new Error(`Refusing to run ${actorId} without a positive maxChargeUsd`);

    const call = {
      actor: actorId, purpose, startedAt: new Date().toISOString(),
      estimatedUsd: round(estimatedUsd), maxChargeUsd: round(maxChargeUsd),
      apifyRunId: null, status: 'starting', items: 0, actualUsd: null, chargedEvents: null,
    };
    this.runRecord.calls.push(call);
    this.onCallUpdate(call);
    this.log.info(`Apify ${purpose}: starting ${actorId} (estimate $${call.estimatedUsd}, hard cap $${call.maxChargeUsd})`);
    try {
      return await this.execute(actorId, input, call, unitPriceUsd, timeoutMs);
    } finally {
      this.onCallUpdate(call);
    }
  }

  async execute(actorId, input, call, unitPriceUsd, timeoutMs) {
    const started = await this.request('POST', `/acts/${actorId}/runs?maxTotalChargeUsd=${call.maxChargeUsd}`, input);
    let run = started.data;
    call.apifyRunId = run.id;
    const t0 = Date.now();
    while (!TERMINAL.has(run.status)) {
      if (Date.now() - t0 > timeoutMs) {
        call.status = 'timed_out_waiting';
        throw new Error(`Apify run ${run.id} did not finish within ${timeoutMs / 60000} minutes`);
      }
      run = (await this.request('GET', `/actor-runs/${run.id}?waitForFinish=60`)).data;
    }
    call.status = run.status.toLowerCase();

    let items = [];
    if (run.defaultDatasetId) {
      items = (await this.request('GET', `/datasets/${run.defaultDatasetId}/items?clean=true`)) || [];
    }
    // Pay-per-event charges post several seconds after the run ends. Poll until they cover the returned
    // items, and never record less than items x unit price, so budget checks cannot see a false $0.
    call.items = items.length;
    const floor = items.length * unitPriceUsd;
    let settled = run;
    for (let i = 0; i < 8; i++) {
      await sleep(4000);
      settled = (await this.request('GET', `/actor-runs/${run.id}`)).data || settled;
      if ((settled.usageTotalUsd || 0) >= floor * 0.99) break;
    }
    call.settled = (settled.usageTotalUsd || 0) >= floor * 0.99;
    call.actualUsd = round(Math.max(settled.usageTotalUsd || 0, floor));
    call.chargedEvents = settled.chargedEventCounts || null;
    this.log.info(`Apify ${call.purpose}: ${call.status}, ${items.length} items, charged $${call.actualUsd}`);
    if (run.status !== 'SUCCEEDED') throw new Error(`Apify run ${run.id} ended with ${run.status}`);
    return items;
  }
}

module.exports = { ApifyReader, ALLOWED_ACTORS };
