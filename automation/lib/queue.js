'use strict';

// The approval/publish state machine for daily comment candidates. Pure and synchronous except
// for `publish`, which calls out to an injected `publishOne` (network happens only there, never
// inside `approve`). Nothing in this file talks to Publora directly — see lib/publora.js for that.

const STATUS = Object.freeze({
  AWAITING_APPROVAL: 'AWAITING_APPROVAL',
  APPROVED: 'APPROVED',
  PUBLISHING: 'PUBLISHING',
  PUBLISHED: 'PUBLISHED',
  FAILED: 'FAILED',
});

function buildItems(report, cachePosts, now) {
  return report.candidates.map((c) => {
    const cached = cachePosts[c.postId] || {};
    return {
      n: c.rank,
      postId: c.postId,
      author: c.author.name,
      authorHeadline: c.author.headline || '',
      url: c.url,
      reactions: c.reactions,
      comments: c.comments,
      postedId: `urn:li:activity:${c.postId}`,
      fallbackPostedId: cached.shareUrn || null,
      message: c.draft,
      chars: c.draftChars,
      status: STATUS.AWAITING_APPROVAL,
      createdAt: now.toISOString(),
      approvedAt: null,
      approvedNote: null,
      publishedAt: null,
      publoraResult: null,
      history: [{ at: now.toISOString(), from: null, to: STATUS.AWAITING_APPROVAL, note: 'generated from daily candidates' }],
    };
  });
}

// Builds a fresh queue from today's daily_candidates report. Every item starts AWAITING_APPROVAL.
// This never marks anything approved or published — that only happens through approve()/publish().
// This module is deliberately network-agnostic: `endpoint` is just a display label supplied by
// the caller (publish-cli.js), never a URL this file calls itself.
function buildQueue(report, cachePosts, { now = new Date(), account = null, endpoint = null } = {}) {
  if (!report || !Array.isArray(report.candidates)) throw new Error('buildQueue: report.candidates is required');
  return {
    date: report.date,
    createdAt: now.toISOString(),
    updatedAt: now.toISOString(),
    account,
    endpoint,
    items: buildItems(report, cachePosts, now),
  };
}

// Re-running "build" (e.g. after --refresh added new candidates) must not reset an item that has
// already been approved or published. Items are matched by postId; anything already tracked keeps
// its existing record untouched, and only genuinely new postIds are added as AWAITING_APPROVAL.
function mergeQueue(existingQueue, freshQueue) {
  if (!existingQueue) return freshQueue;
  const known = new Map(existingQueue.items.map((i) => [i.postId, i]));
  const items = freshQueue.items.map((fresh) => known.get(fresh.postId) || fresh);
  return { ...existingQueue, updatedAt: freshQueue.createdAt, items };
}

function findItem(queue, n) {
  return queue.items.find((i) => i.n === n);
}

function pushHistory(item, to, note, now) {
  const from = item.status;
  item.status = to;
  item.history.push({ at: now.toISOString(), from, to, note });
}

/**
 * Approve item(s). selector is exactly one of:
 *   { all: true }   - approve every item currently AWAITING_APPROVAL; anything already
 *                      approved/published/failed is left as-is (skipped, not an error).
 *   { ids: [n,...] } - approve only these specific item numbers. Every named id must currently
 *                      be AWAITING_APPROVAL, or the WHOLE call is refused and nothing changes
 *                      (no partial approval). Approving item #7 never touches item #1: only the
 *                      ids explicitly listed are ever mutated.
 * `note` is a free-text record of what triggered the approval (e.g. the user's own words), stored
 * on each approved item for the audit trail. Never called implicitly — every approval requires an
 * explicit selector supplied by the caller in direct response to the user.
 */
function approve(queue, selector, note, now = new Date()) {
  if (!selector || (selector.all !== true && !(Array.isArray(selector.ids) && selector.ids.length))) {
    throw new Error('approve: selector must be {all:true} or {ids:[n,...]} with at least one id');
  }
  const approved = [];
  const skipped = [];

  if (selector.all) {
    for (const item of queue.items) {
      if (item.status === STATUS.AWAITING_APPROVAL) {
        pushHistory(item, STATUS.APPROVED, note, now);
        item.approvedAt = now.toISOString();
        item.approvedNote = note;
        approved.push(item.n);
      } else {
        skipped.push({ n: item.n, status: item.status });
      }
    }
  } else {
    const ids = [...new Set(selector.ids)];
    // Validate every id before mutating any of them: an explicit "approve #7" must never
    // half-apply, and must never move a second item just because it happened to be in the list.
    const targets = ids.map((n) => {
      const item = findItem(queue, n);
      if (!item) throw new Error(`approve: no item #${n} in this queue`);
      if (item.status !== STATUS.AWAITING_APPROVAL) {
        throw new Error(`approve: item #${n} is ${item.status}, not AWAITING_APPROVAL; refusing the whole request, nothing was changed`);
      }
      return item;
    });
    for (const item of targets) {
      pushHistory(item, STATUS.APPROVED, note, now);
      item.approvedAt = now.toISOString();
      item.approvedNote = note;
      approved.push(item.n);
    }
  }

  queue.updatedAt = now.toISOString();
  return { approved, skipped };
}

/**
 * Publish item(s) by calling `publishOne(item)` for each target and recording the result.
 * selector is exactly one of:
 *   { all: true }    - publish every item currently APPROVED (0 or more). Items in any other
 *                       state (including AWAITING_APPROVAL) are left completely untouched.
 *   { ids: [n,...] } - publish only these specific item numbers. Every named id must currently
 *                       be APPROVED, or the WHOLE call is refused before a single network call is
 *                       made (no partial publish, nothing marked PUBLISHING). This is what makes
 *                       "approve #7, then publish #1" a safe no-op error instead of a leak.
 * A per-item failure (publishOne rejects) does not stop the rest of the batch: it is recorded as
 * FAILED on that item and the loop continues.
 */
async function publish(queue, selector, { publishOne, now = new Date() } = {}) {
  if (typeof publishOne !== 'function') throw new Error('publish: publishOne callback is required');
  if (!selector || (selector.all !== true && !(Array.isArray(selector.ids) && selector.ids.length))) {
    throw new Error('publish: selector must be {all:true} or {ids:[n,...]} with at least one id');
  }

  let targets;
  if (selector.all) {
    targets = queue.items.filter((i) => i.status === STATUS.APPROVED);
  } else {
    const ids = [...new Set(selector.ids)];
    targets = ids.map((n) => {
      const item = findItem(queue, n);
      if (!item) throw new Error(`publish: no item #${n} in this queue`);
      if (item.status !== STATUS.APPROVED) {
        throw new Error(`publish: item #${n} is ${item.status}, not APPROVED; refusing the whole request. Nothing was published.`);
      }
      return item;
    });
  }

  const targetSet = new Set(targets);
  const published = [];
  const failed = [];
  for (const item of targets) {
    pushHistory(item, STATUS.PUBLISHING, 'publish requested', now);
    try {
      // eslint-disable-next-line no-await-in-loop
      const result = await publishOne(item);
      item.publoraResult = result;
      item.publishedAt = now.toISOString();
      pushHistory(item, STATUS.PUBLISHED, 'publora accepted', now);
      published.push(item.n);
    } catch (err) {
      item.publoraResult = { error: err.message };
      pushHistory(item, STATUS.FAILED, err.message, now);
      failed.push({ n: item.n, error: err.message });
    }
  }

  queue.updatedAt = now.toISOString();
  const untouched = queue.items.filter((i) => !targetSet.has(i)).map((i) => i.n);
  return { published, failed, untouched };
}

module.exports = { STATUS, buildQueue, mergeQueue, approve, publish, findItem };
