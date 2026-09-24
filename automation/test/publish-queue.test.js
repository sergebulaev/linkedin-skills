'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const core = require('../lib/core');
const queueLib = require('../lib/queue');
const { STATUS } = queueLib;
const publishCli = require('../publish-cli');

const NOW = new Date('2026-09-16T12:00:00Z');

function fakeReport(n = 10) {
  return {
    date: '2026-09-16',
    status: 'complete',
    candidates: Array.from({ length: n }, (_, i) => ({
      rank: i + 1,
      postId: `750500000000000${String(i).padStart(3, '0')}`,
      author: { name: `Author ${i + 1}`, headline: 'Engineer' },
      url: `https://www.linkedin.com/posts/author-${i + 1}_topic-activity-750500000000000${String(i).padStart(3, '0')}-abcd`,
      reactions: 200 - i * 5,
      comments: 20 + i,
      draft: `Draft comment number ${i + 1} with a concrete technical point about backend engineering.`,
      draftChars: 90,
    })),
  };
}

function fakeCache(report) {
  const posts = {};
  for (const c of report.candidates) posts[c.postId] = { shareUrn: `urn:li:share:${c.postId}` };
  return { posts };
}

function freshQueue(n = 10) {
  const report = fakeReport(n);
  return queueLib.buildQueue(report, fakeCache(report).posts, { now: NOW });
}

// A publishOne stub that records every call it receives, in order, and never touches the network.
function recordingPublisher(behavior = {}) {
  const calls = [];
  const fn = async (item) => {
    calls.push(item.n);
    if (behavior.failFor && behavior.failFor.includes(item.n)) throw new Error(`simulated Publora failure for #${item.n}`);
    return { httpStatus: 201, body: { success: true, comment: { id: `fake-${item.n}`, message: item.message } } };
  };
  fn.calls = calls;
  return fn;
}

test('buildQueue: every candidate starts AWAITING_APPROVAL with the exact drafted text', () => {
  const report = fakeReport(10);
  const q = queueLib.buildQueue(report, fakeCache(report).posts, { now: NOW });
  assert.equal(q.items.length, 10);
  for (const [i, item] of q.items.entries()) {
    assert.equal(item.status, STATUS.AWAITING_APPROVAL);
    assert.equal(item.n, i + 1);
    assert.equal(item.message, report.candidates[i].draft);
    assert.equal(item.postedId, `urn:li:activity:${report.candidates[i].postId}`);
    assert.equal(item.approvedAt, null);
    assert.equal(item.publishedAt, null);
    assert.equal(item.publoraResult, null);
  }
});

test('approve #7 only: item 7 becomes APPROVED, every other item is untouched', () => {
  const q = freshQueue(10);
  const { approved, skipped } = queueLib.approve(q, { ids: [7] }, 'user said: Publish #7', NOW);
  assert.deepEqual(approved, [7]);
  assert.deepEqual(skipped, []);
  for (const item of q.items) {
    if (item.n === 7) {
      assert.equal(item.status, STATUS.APPROVED);
      assert.equal(item.approvedNote, 'user said: Publish #7');
    } else {
      assert.equal(item.status, STATUS.AWAITING_APPROVAL, `item #${item.n} must stay AWAITING_APPROVAL`);
      assert.equal(item.approvedAt, null);
    }
  }
});

test('approve: unknown id throws and changes nothing', () => {
  const q = freshQueue(10);
  assert.throws(() => queueLib.approve(q, { ids: [999] }, 'x', NOW), /no item #999/);
  assert.ok(q.items.every((i) => i.status === STATUS.AWAITING_APPROVAL));
});

test('approve: naming an already-approved id a second time throws and approves nothing new', () => {
  const q = freshQueue(10);
  queueLib.approve(q, { ids: [7] }, 'first', NOW);
  assert.throws(() => queueLib.approve(q, { ids: [7, 2] }, 'second', NOW), /item #7 is APPROVED, not AWAITING_APPROVAL/);
  // The whole call was refused: #2 must NOT have been approved either, even though it was valid.
  assert.equal(queueLib.findItem(q, 2).status, STATUS.AWAITING_APPROVAL);
  assert.equal(queueLib.findItem(q, 7).status, STATUS.APPROVED);
});

test('approve all: every AWAITING_APPROVAL item moves to APPROVED in one explicit action', () => {
  const q = freshQueue(10);
  const { approved, skipped } = queueLib.approve(q, { all: true }, 'user said: I approve all 10 generated comment drafts', NOW);
  assert.deepEqual(approved, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  assert.deepEqual(skipped, []);
  assert.ok(q.items.every((i) => i.status === STATUS.APPROVED));
});

test('approve all after one item is already approved: leaves that item alone, approves the rest', () => {
  const q = freshQueue(10);
  queueLib.approve(q, { ids: [7] }, 'first', NOW);
  const { approved, skipped } = queueLib.approve(q, { all: true }, 'rest', NOW);
  assert.equal(approved.includes(7), false, 'item 7 was already approved, "all" must not re-approve it');
  assert.equal(approved.length, 9);
  assert.deepEqual(skipped, [{ n: 7, status: STATUS.APPROVED }]);
});

test('publish: refuses an item that is not APPROVED, and calls Publora zero times', async () => {
  const q = freshQueue(10);
  const pub = recordingPublisher();
  await assert.rejects(
    queueLib.publish(q, { ids: [1] }, { publishOne: pub, now: NOW }),
    /item #1 is AWAITING_APPROVAL, not APPROVED/,
  );
  assert.deepEqual(pub.calls, []);
  assert.equal(queueLib.findItem(q, 1).status, STATUS.AWAITING_APPROVAL);
});

test('THE BUG: approving #7 only, then publishing "all", publishes ONLY #7 - #1 is never touched', async () => {
  const q = freshQueue(10);
  queueLib.approve(q, { ids: [7] }, 'user said: Publish #7', NOW);
  const pub = recordingPublisher();
  const { published, failed, untouched } = await queueLib.publish(q, { all: true }, { publishOne: pub, now: NOW });

  assert.deepEqual(pub.calls, [7], 'Publora must be called exactly once, for item 7 only');
  assert.deepEqual(published, [7]);
  assert.deepEqual(failed, []);
  assert.ok(untouched.includes(1), 'item 1 must be reported as untouched');

  const item1 = queueLib.findItem(q, 1);
  assert.equal(item1.status, STATUS.AWAITING_APPROVAL, 'item 1 must remain AWAITING_APPROVAL, never PUBLISHED');
  assert.equal(item1.publishedAt, null);
  assert.equal(item1.publoraResult, null);

  const item7 = queueLib.findItem(q, 7);
  assert.equal(item7.status, STATUS.PUBLISHED);
  assert.ok(item7.publishedAt);
});

test('THE BUG, second form: approving #7 only, then explicitly publishing #1, is refused and publishes nothing', async () => {
  const q = freshQueue(10);
  queueLib.approve(q, { ids: [7] }, 'user said: Publish #7', NOW);
  const pub = recordingPublisher();
  await assert.rejects(
    queueLib.publish(q, { ids: [1] }, { publishOne: pub, now: NOW }),
    /item #1 is AWAITING_APPROVAL, not APPROVED/,
  );
  assert.deepEqual(pub.calls, [], 'Publora must never be called for an unapproved item');
  assert.equal(queueLib.findItem(q, 1).status, STATUS.AWAITING_APPROVAL);
  assert.equal(queueLib.findItem(q, 7).status, STATUS.APPROVED, 'the earlier approval of #7 must be unaffected by the refused #1 request');
});

test('approve all, then publish all: every one of the 10 items is published, in order, with its own text', async () => {
  const q = freshQueue(10);
  queueLib.approve(q, { all: true }, 'user said: I approve all 10 generated comment drafts', NOW);
  const pub = recordingPublisher();
  const { published, failed } = await queueLib.publish(q, { all: true }, { publishOne: pub, now: NOW });
  assert.deepEqual(pub.calls, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  assert.deepEqual(published, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  assert.deepEqual(failed, []);
  for (const item of q.items) {
    assert.equal(item.status, STATUS.PUBLISHED);
    assert.equal(item.publoraResult.body.comment.message, item.message);
  }
});

test('publish: a per-item Publora failure does not block the rest of the approved batch', async () => {
  const q = freshQueue(5);
  queueLib.approve(q, { all: true }, 'approve all', NOW);
  const pub = recordingPublisher({ failFor: [3] });
  const { published, failed } = await queueLib.publish(q, { all: true }, { publishOne: pub, now: NOW });
  assert.deepEqual(published, [1, 2, 4, 5]);
  assert.deepEqual(failed, [{ n: 3, error: 'simulated Publora failure for #3' }]);
  assert.equal(queueLib.findItem(q, 3).status, STATUS.FAILED);
  assert.equal(queueLib.findItem(q, 1).status, STATUS.PUBLISHED);
});

test('publish "all" is idempotent: already-published items are never re-submitted', async () => {
  const q = freshQueue(3);
  queueLib.approve(q, { all: true }, 'approve all', NOW);
  const pub = recordingPublisher();
  await queueLib.publish(q, { all: true }, { publishOne: pub, now: NOW });
  assert.deepEqual(pub.calls, [1, 2, 3]);
  const { published } = await queueLib.publish(q, { all: true }, { publishOne: pub, now: NOW });
  assert.deepEqual(published, [], 'a second "publish all" must find nothing left in APPROVED state');
  assert.deepEqual(pub.calls, [1, 2, 3], 'Publora must not be called again for already-published items');
});

test('mergeQueue: rebuilding the queue never resets an approved or published item', () => {
  const q1 = freshQueue(5);
  queueLib.approve(q1, { ids: [2] }, 'approved earlier', NOW);
  const report = fakeReport(5);
  const fresh = queueLib.buildQueue(report, fakeCache(report).posts, { now: new Date(NOW.getTime() + 3600000) });
  const merged = queueLib.mergeQueue(q1, fresh);
  assert.equal(queueLib.findItem(merged, 2).status, STATUS.APPROVED, 'rebuilding must not revert an approved item to AWAITING_APPROVAL');
  assert.equal(queueLib.findItem(merged, 1).status, STATUS.AWAITING_APPROVAL);
});

// --- CLI-level tests: exercise the actual commands a person/agent runs, still with zero network ---

function tmpDirs() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'li-publish-cli-'));
  return { output: path.join(tmp, 'output'), state: path.join(tmp, 'state'), logs: path.join(tmp, 'logs'), _tmp: tmp };
}

function writeFixture(dirs, n = 10) {
  const report = fakeReport(n);
  core.writeJson(path.join(dirs.output, `daily_candidates_${report.date}.json`), report);
  core.writeJson(path.join(dirs.state, 'posts_cache.json'), fakeCache(report));
  return report;
}

test('CLI: build never calls Publora and saves every item AWAITING_APPROVAL', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 10);
  const res = await publishCli.main(['build'], { dirs, now: NOW });
  assert.equal(res.status, 'ok');
  assert.equal(res.queue.items.length, 10);
  assert.ok(res.queue.items.every((i) => i.status === STATUS.AWAITING_APPROVAL));
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});

test('CLI: publish before any approval is refused', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 10);
  await publishCli.main(['build'], { dirs, now: NOW });
  const pub = recordingPublisher();
  await assert.rejects(publishCli.main(['publish', '5'], { dirs, now: NOW, publishOne: pub }), /item #5 is AWAITING_APPROVAL, not APPROVED/);
  assert.deepEqual(pub.calls, []);
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});

test('CLI: "approve 7" then "publish 7" publishes only #7; "publish all" afterward finds nothing else approved', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 10);
  await publishCli.main(['build'], { dirs, now: NOW });
  await publishCli.main(['approve', '7'], { dirs, now: NOW });

  const pub = recordingPublisher();
  const res = await publishCli.main(['publish', '7'], { dirs, now: NOW, publishOne: pub });
  assert.deepEqual(res.published, [7]);
  assert.deepEqual(pub.calls, [7]);

  const again = await publishCli.main(['publish', 'all'], { dirs, now: NOW, publishOne: pub });
  assert.deepEqual(again.published, [], '#1..#6 and #8..#10 were never approved, so "publish all" must publish nothing more');
  assert.deepEqual(pub.calls, [7]);

  const shown = await publishCli.main(['show'], { dirs, now: NOW });
  assert.equal(queueLib.findItem(shown.queue, 1).status, STATUS.AWAITING_APPROVAL);
  assert.equal(queueLib.findItem(shown.queue, 7).status, STATUS.PUBLISHED);
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});

test('CLI: "approve all" then "publish all" publishes all 10, in the order requested', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 10);
  await publishCli.main(['build'], { dirs, now: NOW });
  const approveRes = await publishCli.main(['approve', 'all'], { dirs, now: NOW });
  assert.equal(approveRes.approved.length, 10);

  const pub = recordingPublisher();
  const res = await publishCli.main(['publish', 'all'], { dirs, now: NOW, publishOne: pub });
  assert.deepEqual(res.published, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  assert.deepEqual(pub.calls, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});

test('CLI safety: build/show/approve never touch the network, even with global fetch stubbed to throw', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 10);
  const originalFetch = global.fetch;
  global.fetch = () => { throw new Error('network must not be touched by build/show/approve'); };
  try {
    await publishCli.main(['build'], { dirs, now: NOW });
    await publishCli.main(['show'], { dirs, now: NOW });
    await publishCli.main(['approve', '7'], { dirs, now: NOW });
    await publishCli.main(['approve', 'all'], { dirs, now: NOW });
  } finally {
    global.fetch = originalFetch;
  }
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});

test('CLI: publish with no Publora credentials and no override refuses before any call (never touches the real .env)', async () => {
  const dirs = tmpDirs();
  writeFixture(dirs, 3);
  await publishCli.main(['build'], { dirs, now: NOW });
  await publishCli.main(['approve', 'all'], { dirs, now: NOW });
  const originalFetch = global.fetch;
  global.fetch = () => { throw new Error('network must not be touched when credentials are missing'); };
  // A fake, empty env function stands in for core.loadEnv() so this test is independent of
  // whatever is actually configured in this machine's real .env.
  const emptyEnv = () => '';
  try {
    await assert.rejects(
      publishCli.main(['publish', 'all'], { dirs, now: NOW, env: emptyEnv }),
      /PUBLORA_API_KEY and LINKEDIN_PLATFORM_ID must both be set/,
    );
  } finally {
    global.fetch = originalFetch;
  }
  fs.rmSync(dirs._tmp, { recursive: true, force: true });
});
