#!/usr/bin/env node
'use strict';

// Draft -> approve -> publish workflow for today's comment candidates. This is the ONLY place
// that can call Publora, and only the "publish" command does so, and only for items whose status
// is already APPROVED. "build", "show" and "approve" never make a network call to LinkedIn/Publora.
//
// State lives in automation/output/publish_queue_<date>.json, one record per candidate, with an
// explicit status: AWAITING_APPROVAL -> APPROVED -> PUBLISHING -> PUBLISHED | FAILED. Approving
// one item only ever changes that item; nothing is inferred from a previous command.

const path = require('path');
const core = require('./lib/core');
const queueLib = require('./lib/queue');
const { makePublishOne } = require('./lib/publora');
const render = require('./lib/render');

const HELP = `Usage: node automation/publish-cli.js <command> [args] [--date=YYYY-MM-DD]

  build          Build/refresh today's publish queue from daily_candidates_<date>.json.
                 New items start AWAITING_APPROVAL. Items already approved or published keep
                 their existing state (build never resets or re-publishes anything).
  show           Print every item in today's queue with its current status.
  approve <n>    Approve exactly one item by its # (e.g. "approve 7"). No other item changes.
  approve all    Approve every item currently AWAITING_APPROVAL. You must type "all".
  publish <n>    Publish item #n via Publora. Refuses and publishes nothing unless #n is
                 already APPROVED.
  publish all    Publish every item currently APPROVED. Anything not approved is left alone.

Only "publish" ever calls Publora, and only for items already APPROVED. "approve #7" approves
item 7 and nothing else; it never approves or publishes any other item.
`;

function printQueue(q) {
  console.log(`\nQueue for ${q.date} (updated ${q.updatedAt}):\n`);
  for (const i of q.items) {
    console.log(`  #${i.n} [${i.status}] ${i.author} (${i.reactions} rx, ${i.comments} cm) - ${i.url}`);
  }
  const counts = q.items.reduce((m, i) => ({ ...m, [i.status]: (m[i.status] || 0) + 1 }), {});
  console.log(`\n  Totals: ${Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(', ')}\n`);
}

function queuePath(dirs, date) {
  return path.join(dirs.output, `publish_queue_${date}.json`);
}

function loadQueueOrThrow(dirs, date) {
  const q = core.readJson(queuePath(dirs, date), null);
  if (!q) throw new Error(`No publish queue for ${date} yet. Run "node automation/publish-cli.js build" first.`);
  return q;
}

function parseSelector(arg, label) {
  if (arg === 'all') return { all: true };
  const n = Number(arg);
  if (!Number.isInteger(n) || n <= 0) throw new Error(`${label}: "${arg}" is not a valid item number or "all"`);
  return { ids: [n] };
}

function cmdBuild(dirs, date) {
  const reportFile = path.join(dirs.output, `daily_candidates_${date}.json`);
  const report = core.readJson(reportFile, null);
  if (!report) throw new Error(`No candidates file for ${date} (${reportFile}). Run run-daily.js first.`);
  if (report.status !== 'complete') throw new Error(`Today's candidates are not complete (status: ${report.status}). Run run-daily.js again before building the publish queue.`);
  const cache = core.readJson(path.join(dirs.state, 'posts_cache.json'), { posts: {} });
  const env = core.loadEnv();
  const account = env('LINKEDIN_PLATFORM_ID') ? `Publora channel ${env('LINKEDIN_PLATFORM_ID')}` : null;
  const fresh = queueLib.buildQueue(report, cache.posts, { account, endpoint: 'POST https://api.publora.com/api/v1/linkedin-comments' });
  const existing = core.readJson(queuePath(dirs, date), null);
  const merged = queueLib.mergeQueue(existing, fresh);
  core.writeJson(queuePath(dirs, date), merged);
  core.writeText(path.join(dirs.output, `publish_queue_${date}.md`), render.renderQueueMarkdown(merged));
  console.log(`Saved ${merged.items.length} item(s), all reviewable in ${queuePath(dirs, date)}`);
  printQueue(merged);
  return merged;
}

function cmdShow(dirs, date) {
  const q = loadQueueOrThrow(dirs, date);
  printQueue(q);
  return q;
}

function cmdApprove(dirs, date, arg, now) {
  const q = loadQueueOrThrow(dirs, date);
  const selector = parseSelector(arg, 'approve');
  const note = `approved via CLI: "${arg}"`;
  const { approved, skipped } = queueLib.approve(q, selector, note, now);
  core.writeJson(queuePath(dirs, date), q);
  core.writeText(path.join(dirs.output, `publish_queue_${date}.md`), render.renderQueueMarkdown(q));
  console.log(`Approved: ${approved.length ? approved.map((n) => `#${n}`).join(', ') : 'none'}`);
  if (skipped.length) console.log(`Left unchanged (not AWAITING_APPROVAL): ${skipped.map((s) => `#${s.n} (${s.status})`).join(', ')}`);
  printQueue(q);
  return { queue: q, approved, skipped };
}

async function cmdPublish(dirs, date, arg, now, publishOneOverride, envFn) {
  const q = loadQueueOrThrow(dirs, date);
  const selector = parseSelector(arg, 'publish');
  let publishOne = publishOneOverride;
  if (!publishOne) {
    const env = envFn || core.loadEnv();
    const apiKey = env('PUBLORA_API_KEY');
    const platformId = env('LINKEDIN_PLATFORM_ID');
    if (!apiKey || !platformId) throw new Error('PUBLORA_API_KEY and LINKEDIN_PLATFORM_ID must both be set (in .env) to publish.');
    publishOne = makePublishOne({ apiKey, platformId });
  }
  const { published, failed, untouched } = await queueLib.publish(q, selector, { publishOne, now });
  core.writeJson(queuePath(dirs, date), q);
  core.writeText(path.join(dirs.output, `publish_queue_${date}.md`), render.renderQueueMarkdown(q));
  console.log(`Published: ${published.length ? published.map((n) => `#${n}`).join(', ') : 'none'}`);
  if (failed.length) console.log(`Failed: ${failed.map((f) => `#${f.n}: ${f.error}`).join('; ')}`);
  console.log(`Untouched (not part of this request): ${untouched.length}`);
  printQueue(q);
  return { queue: q, published, failed, untouched };
}

async function main(argv, overrides = {}) {
  const [command, arg] = argv.filter((a) => !a.startsWith('--'));
  if (!command || command === '--help' || command === '-h') { console.log(HELP); return { status: 'help' }; }

  const config = overrides.config || core.loadConfig();
  const now = overrides.now || new Date();
  const dirs = overrides.dirs || core.defaultDirs('live');
  const dateFlag = argv.find((a) => a.startsWith('--date='));
  const date = dateFlag ? dateFlag.slice('--date='.length) : core.localDate(now, config.timezone);

  if (command === 'build') return { status: 'ok', queue: cmdBuild(dirs, date) };
  if (command === 'show') return { status: 'ok', queue: cmdShow(dirs, date) };
  if (command === 'approve') {
    if (!arg) throw new Error(`${HELP}\napprove requires an item number or "all"`);
    return { status: 'ok', ...cmdApprove(dirs, date, arg, now) };
  }
  if (command === 'publish') {
    if (!arg) throw new Error(`${HELP}\npublish requires an item number or "all"`);
    return { status: 'ok', ...(await cmdPublish(dirs, date, arg, now, overrides.publishOne, overrides.env)) };
  }
  throw new Error(`Unknown command "${command}"\n\n${HELP}`);
}

if (require.main === module) {
  main(process.argv.slice(2)).then(
    () => { process.exitCode = 0; },
    (err) => { console.error(err.message); process.exitCode = 1; },
  );
}

module.exports = { main };
