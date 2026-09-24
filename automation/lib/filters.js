'use strict';

const ID_RE = /(?:activity|ugcPost|share)[-:](\d{18,22})/;

function idFromUrl(url) {
  const m = String(url || '').match(ID_RE);
  return m ? m[1] : null;
}

function timestampFromActivityId(id) {
  try { return Number(BigInt(id) >> 22n); } catch { return null; }
}

function cleanUrl(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    return `${u.origin}${u.pathname}`;
  } catch {
    return String(url).split('?')[0];
  }
}

function profileUrlOf(author) {
  if (!author) return null;
  if (author.publicIdentifier) return `https://www.linkedin.com/in/${author.publicIdentifier}/`;
  const url = cleanUrl(author.linkedinUrl);
  return url && /linkedin\.com\/in\//.test(url) ? url : null;
}

// harvestapi post items (search and profile-posts share this shape) -> internal post record.
function normalizePost(item, source, fetchedAt) {
  if (!item || (item.type && item.type !== 'post')) return null;
  const url = cleanUrl(item.linkedinUrl);
  const id = String(item.id || idFromUrl(item.linkedinUrl) || '');
  if (!/^\d{18,22}$/.test(id)) return null;
  const author = item.author || {};
  const eng = item.engagement || {};
  const header = item.header || {};
  return {
    id,
    url,
    shareUrn: item.shareUrn || null,
    author: {
      name: author.name || 'Unknown',
      headline: author.info || author.position || '',
      type: author.type || 'profile',
      profileUrl: profileUrlOf(author),
    },
    content: String(item.content || '').slice(0, 4000),
    postedAtMs: (item.postedAt && item.postedAt.timestamp) || timestampFromActivityId(id),
    reactions: Number(eng.likes || 0),
    comments: Number(eng.comments || 0),
    shares: Number(eng.shares || 0),
    engagementAt: fetchedAt,
    isJob: Boolean(item.job),
    headerText: header.text || '',
    sources: [source],
  };
}

const JOB_RE = /\b(we('|’)?re hiring|we are hiring|now hiring|is hiring|hiring (for|a|an)\b|job opening|open (role|position)s?|apply (now|here|via|at|today)|immediate joiners?|notice period|ctc\b|salary range|send (your )?(cv|resume))|#hiring\b/i;
const GROUP_HEADER_RE = /^new post in /i;
const GIVEAWAY_RE = /\bcomment\s+["“']?[\w-]{2,20}["”']?\s+(below\s+)?(and|&)\s+i('|’)?ll\s+(send|share|dm)|\bcomment\s+["“']?[\w-]{2,20}["”']?\s+to\s+(get|receive)\b/i;
const PROMO_RES = [
  /\bfree trial\b/i, /\bsign ?up (now|today|free|here)\b/i, /\bbook a (demo|call)\b/i, /\buse (my |the )?code\b/i,
  /\b\d{1,2}% off\b/i, /\blimited[- ]time\b/i, /\bnow live\b/i, /\b(excited|thrilled|proud) to (announce|launch|introduce)\b/i,
  /\bintroducing\b/i, /\blink in (the )?(first )?comments?\b/i, /\b(join|subscribe to) (my|our) (free )?newsletter\b/i,
  /\bdownload (the|our|my) (free )?(guide|ebook|e-book|playbook|report)\b/i, /\bdm (me|us) for\b/i, /\bwaitlist\b/i,
  /\bregister (now|here|today)\b/i, /\b(check out|buy|order|grab) (my|our) (new )?(book|course|product|tool)\b/i,
  /\btry it (for )?(free|now|today)\b/i, /\bis live\b/i,
];

// Creators routinely end technical posts with a P.S. plugging a newsletter or book. That tail is not
// what the post is about, so promo signals are only counted before it.
function promoBody(text) {
  const idx = text.search(/(^|\n)\s*(p\.?\s?s\.?\s*[-:–—]?\s|={3,})/i);
  return idx > 200 ? text.slice(0, idx) : text;
}
const MOTIVATIONAL_RE = /\b(never give up|believe in yourself|grateful|gratitude|blessed|dream job|thrilled to (share|announce)|excited to (share|announce)|new (role|position|chapter)|work anniversary|badge|years at|got promoted|promotion|laid off|layoffs?|rejected|my journey|hustle|mindset|motivation|success is|keep going|proud moment)\b/i;

const keywordCache = new Map();
function keywordRegex(kw) {
  if (!keywordCache.has(kw)) {
    const lower = kw.toLowerCase();
    const prefix = lower.endsWith('*');
    const stem = (prefix ? lower.slice(0, -1) : lower).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    keywordCache.set(kw, new RegExp(`(?:^|[^a-z0-9])${stem}${prefix ? '' : '(?:$|[^a-z0-9])'}`, 'i'));
  }
  return keywordCache.get(kw);
}

function heuristicRelevance(text, topics, experienceKeywords) {
  const matchedTopics = [];
  let hits = 0;
  for (const [topic, keywords] of Object.entries(topics)) {
    const n = keywords.filter((kw) => keywordRegex(kw).test(text)).length;
    if (n > 0) { matchedTopics.push(topic); hits += n; }
  }
  const experienceHits = experienceKeywords.filter((kw) => keywordRegex(kw).test(text)).length;
  const experienceMatch = experienceHits >= 2;
  // Breadth and depth both count: a post that goes deep on one topic should not look unrelated.
  const score = Math.min(100, Math.min(60, matchedTopics.length * 15) + Math.min(30, hits * 5) + (experienceMatch ? 10 : 0));
  return { score, matchedTopics, experienceMatch };
}

function latinRatio(text) {
  const letters = text.match(/\p{L}/gu) || [];
  if (letters.length < 40) return 1;
  const latin = text.match(/\p{Script=Latin}/gu) || [];
  return latin.length / letters.length;
}

function classifyPost(post, config, now) {
  const f = config.filters;
  const text = post.content || '';
  const rel = heuristicRelevance(text, config.topics, config.experience.keywords);
  const flags = [];
  const promoHits = PROMO_RES.filter((re) => re.test(promoBody(text)));
  const promoEarly = PROMO_RES.some((re) => re.test(text.slice(0, 280)));
  if (promoHits.length) flags.push(`promo_signals:${promoHits.length}`);
  if (post.reactions >= 200 && post.comments === 0) flags.push('suspicious_engagement');
  const motivational = MOTIVATIONAL_RE.test(text);
  if (motivational) flags.push('career_or_motivational_language');

  const ageHours = post.postedAtMs ? (now.getTime() - post.postedAtMs) / 3600000 : Infinity;
  let excluded = null;
  if (f.excludeGroupPosts && (/groupPost/i.test(`${post.url} ${post.shareUrn}`) || GROUP_HEADER_RE.test(post.headerText))) excluded = 'group_post';
  else if (f.excludeJobPosts && (post.isJob || JOB_RE.test(text))) excluded = 'job_post';
  else if (f.excludeCompanyAuthors && post.author.type === 'company') excluded = 'company_page';
  else if (latinRatio(text) < 0.6) excluded = 'non_english';
  else if (GIVEAWAY_RE.test(text)) excluded = 'comment_gate_giveaway';
  else if (promoHits.length >= 2 || (promoEarly && rel.score < 50)) excluded = 'product_promotion';
  else if (ageHours > f.maxAgeHours) excluded = 'too_old';
  else if (rel.score < f.minHeuristicRelevance) excluded = 'unrelated_to_positioning';
  else if (motivational && rel.score < f.motivationalMaxRelevance) excluded = 'generic_motivational_or_career';

  return {
    excluded,
    qualifiesReactions: post.reactions >= f.minReactions,
    flags,
    ageHours,
    relevance: rel.score,
    matchedTopics: rel.matchedTopics,
    experienceMatch: rel.experienceMatch,
  };
}

// Optional hard filters (off unless configured). Comment counts only grow, so an old snapshot showing
// few comments proves nothing about now: a post whose engagement data is too old cannot pass.
function hardFilterReason(post, config, now) {
  const f = config.filters;
  if (f.maxComments == null) return null;
  const snapshotAgeHours = (now.getTime() - Date.parse(post.engagementAt)) / 3600000;
  if (f.maxEngagementAgeHours != null && !(snapshotAgeHours <= f.maxEngagementAgeHours)) return 'engagement_data_too_old';
  if (post.comments > f.maxComments) return 'too_many_comments';
  return null;
}

// followers: a number, or null when the count could not be verified. Unverified never passes.
function followerFilterReason(followers, config) {
  const min = config.filters.minAuthorFollowers;
  if (min == null) return null;
  if (followers == null) return 'followers_unverified';
  return followers < min ? 'followers_below_min' : null;
}

module.exports = { normalizePost, classifyPost, hardFilterReason, followerFilterReason, heuristicRelevance, idFromUrl, cleanUrl, profileUrlOf, timestampFromActivityId };
