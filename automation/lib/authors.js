'use strict';

const { round } = require('./core');
const { ALLOWED_ACTORS } = require('./apify');

const PROFILE_MODE = 'Profile details no email ($4 per 1k)';

function authorKey(profileUrl) {
  const m = String(profileUrl || '').match(/linkedin\.com\/in\/([^/?#]+)/i);
  return m ? decodeURIComponent(m[1]).toLowerCase() : null;
}

function cachedFollowers(authors, key, config, now) {
  const hit = key && authors.profiles[key];
  if (!hit) return null;
  const fresh = now.getTime() - Date.parse(hit.fetchedAt) <= config.followers.cacheDays * 86400000;
  return fresh ? hit : null;
}

// Fills c.followers (number, or null = unverified) for every candidate. Profiles are looked up only
// when not cached, in candidate order, and only as many as the remaining run budget covers.
async function resolveFollowers({ candidates, authors, apify, config, now, remainingUsd, log, run }) {
  const pricing = config.budget.pricingUsd;
  const missing = [];
  for (const c of candidates) {
    const key = authorKey(c.post.author.profileUrl);
    const hit = cachedFollowers(authors, key, config, now);
    c.followers = hit ? hit.followers : null;
    c.followersFetchedAt = hit ? hit.fetchedAt : null;
    if (!hit && key && !missing.includes(key)) missing.push(key);
  }
  if (!missing.length) return;
  if (!apify) { log.info(`Followers: ${missing.length} author(s) not cached and no Apify calls allowed in this run; they stay unverified`); return; }

  const affordable = Math.max(0, Math.min(config.followers.maxLookupsPerRun, Math.floor((remainingUsd - pricing.actorStart) / pricing.profile)));
  const keys = missing.slice(0, affordable);
  if (keys.length < missing.length) {
    log.warn(`Followers: budget covers ${keys.length} of ${missing.length} lookups; the rest stay unverified`);
    run.notes.push(`follower counts for ${missing.length - keys.length} author(s) not looked up (run budget)`);
  }
  if (!keys.length) return;

  const est = round(keys.length * pricing.profile + pricing.actorStart);
  try {
    const items = await apify.runActor(ALLOWED_ACTORS.PROFILE_DETAILS, {
      publicIdentifiers: keys,
      profileScraperMode: PROFILE_MODE,
    }, { purpose: `author follower counts (${keys.length} profiles)`, estimatedUsd: est, maxChargeUsd: round(Math.min(est * 1.25 + 0.002, Math.max(est, remainingUsd))), unitPriceUsd: pricing.profile });
    const fetchedAt = now.toISOString();
    for (const it of items) {
      const key = String(it.publicIdentifier || '').toLowerCase() || authorKey(it.linkedinUrl);
      if (!key || typeof it.followerCount !== 'number') continue;
      authors.profiles[key] = { followers: it.followerCount, name: [it.firstName, it.lastName].filter(Boolean).join(' '), fetchedAt };
    }
  } catch (err) {
    log.error(`Follower lookup failed: ${err.message}`);
    run.notes.push(`follower lookup failed: ${err.message}`);
  }
  for (const c of candidates) {
    if (c.followers != null) continue;
    const hit = cachedFollowers(authors, authorKey(c.post.author.profileUrl), config, now);
    if (hit) { c.followers = hit.followers; c.followersFetchedAt = hit.fetchedAt; }
  }
}

module.exports = { resolveFollowers, authorKey };
