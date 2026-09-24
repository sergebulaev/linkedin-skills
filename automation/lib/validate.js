'use strict';

// Durable 2026 AI-tell vocabulary from skills/linkedin-humanizer (scrub-rules.md, strict tier).
const AI_VOCAB = [
  'significant', 'crucial', 'crucially', 'notably', 'particularly', 'comprehensive', 'insightful', 'robust',
  'leverage', 'leverages', 'leveraged', 'leveraging', 'foster', 'fosters', 'fostering', 'landscape', 'nuanced',
  'multifaceted', 'holistic', 'streamline', 'streamlined', 'streamlines', 'elevate', 'elevates', 'empower', 'empowers',
  'utilize', 'utilizes', 'utilizing', 'facilitate', 'facilitates', 'harness', 'unlock', 'unlocks', 'navigate',
  'navigating', 'seamless', 'seamlessly', 'ecosystem', 'fundamentally', 'essentially', 'ultimately', 'arguably',
  'undoubtedly', 'delve', 'tapestry', 'realm', 'game-changer', 'deep dive', 'quietly', 'load-bearing',
  'heavy lifting', 'let that sink in', 'at the end of the day', 'testament to', "in today's",
];

const GENERIC_PRAISE = [
  /\bgreat (post|share|read|breakdown|list|write-?up|insights?|points?)\b/i, /\bthanks? (you )?for sharing\b/i,
  /\bvery insightful\b/i, /\blove this\b/i, /\bwell said\b/i, /\bso true\b/i, /\bspot on\b/i,
  /\bcouldn'?t agree more\b/i, /^\s*(this|100%|exactly|absolutely)[.!]/i, /\bamazing (post|content)\b/i,
];
const ENGAGEMENT_BAIT = [
  /\bagree\s*\?/i, /\bthoughts\s*\?/i, /\bwhat do you think\b/i, /\bfollow (me|for more)\b/i, /\bcheck out (my|our)\b/i,
  /\bdm me\b/i, /\blink in (bio|comments?)\b/i, /\brepost (this|if)\b/i, /\btag (someone|a friend)\b/i,
];
const REVEAL_AND_PARALLELISM = [
  /\bit('|’)?s not (just |about )?[^.,;!?]{1,40}, it('|’)?s\b/i, /\bisn('|’)?t [^.,;!?]{1,40}, it('|’)?s\b/i,
  /\bnot [^.,;!?]{1,30}, but\b/i, /\bthis isn('|’)?t [^.!?]{1,40}\. this is\b/i,
  /(^|[.!?]\s+)the (result|lesson|catch|answer|kicker|truth)\?/i, /\bhere('|’)?s (what|how|why|the thing)\b/i,
  /\bplot twist\b/i, /\blet me be (honest|real|clear)\b/i, /\bhonestly\s*\?/i, /\bunpopular opinion\b/i,
];
const EXPERIENCE_FACT_RE = /700\s?MB|100K\+?|100,000\+?/i;
const FIRST_PERSON_CLAIM_RE = /\b(I|I've|I'd|I've|we|we've|our team|my team)\b[^.!?]{0,40}\b(built|processed|shipped|ran|worked (on|through|with)|handled|migrated|designed|implemented|scaled|dealt with|debugged|led|wrote|deployed|used|saw|have seen|had to|hit|fixed|reduced|improved|optimi[sz]ed|managed|created|maintained|ran into|measured|benchmarked|learned|went through)\b/i;
const EXPERIENCE_CONTEXT_RE = /\b(in my experience|at my (company|job|work|previous|last)|at work we|in production we|our (system|service|stack|pipeline|team|codebase))\b/i;
const ADDED_DETAIL_RE = /(\d+(\.\d+)?\s?(%|ms\b|sec\b|seconds|minutes|hours|days|gb\b|x\b))|\b(reduced|cut|dropped|faster|slower|crash(ed|es)?|oom\b|out of memory|kafka|postgres|mongodb|redis|s3\b|aws|gcp|azure|worker threads?|workers?|lambda|kubernetes|in production|at scale|million|(single|one|a single)( node(\.js)?)? (process|machine|server|instance|thread)|cluster(ed)?|multi-?thread\w*|last (year|month|week)|at (work|my job)|for a client|on a laptop)\b/i;

function sentences(text) {
  return text.split(/(?<=[.!?])\s+/).filter(Boolean);
}

function validateDraft(draft, { minChars, maxChars }) {
  const errors = [];
  const warnings = [];
  const text = String(draft || '').trim();
  const chars = [...text].length;

  if (!text) errors.push('empty_draft');
  if (chars && chars < 150) errors.push(`too_short:${chars}`);
  else if (chars && chars < minChars) warnings.push(`below_${minChars}_chars:${chars}`);
  if (chars > 420) errors.push(`too_long:${chars}`);
  else if (chars > maxChars) warnings.push(`above_${maxChars}_chars:${chars}`);

  if (/(^|\s)#[\p{L}\p{N}_]+/u.test(text)) errors.push('hashtag');
  if (/\p{Extended_Pictographic}/u.test(text)) errors.push('emoji');
  if (/https?:\/\/|www\./i.test(text)) errors.push('link');
  if (/(^|\s)@[\p{L}\w]/u.test(text)) errors.push('mention');
  if ((text.match(/—/g) || []).length > 1) errors.push('em_dash_over_cap');
  if (/\s–\s|\s--\s/.test(text)) warnings.push('dash_between_clauses');

  const lower = text.toLowerCase();
  const vocab = AI_VOCAB.filter((w) => new RegExp(`(^|[^a-z])${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^a-z]|$)`, 'i').test(lower));
  if (vocab.length >= 2) errors.push(`ai_vocabulary:${vocab.join(',')}`);
  else if (vocab.length === 1) warnings.push(`ai_vocabulary:${vocab[0]}`);

  for (const re of GENERIC_PRAISE) if (re.test(text)) { errors.push('generic_praise'); break; }
  for (const re of ENGAGEMENT_BAIT) if (re.test(text)) { errors.push('engagement_bait'); break; }
  for (const re of REVEAL_AND_PARALLELISM) if (re.test(text)) { errors.push('ai_phrasing_pattern'); break; }

  const usesExperience = EXPERIENCE_FACT_RE.test(text);
  for (const s of sentences(text)) {
    const claims = FIRST_PERSON_CLAIM_RE.test(s) || EXPERIENCE_CONTEXT_RE.test(s);
    if (claims && !EXPERIENCE_FACT_RE.test(s)) errors.push(`possible_invented_experience:"${s.slice(0, 80)}"`);
    if (EXPERIENCE_FACT_RE.test(s) && ADDED_DETAIL_RE.test(s)) errors.push(`experience_detail_not_provided:"${s.slice(0, 80)}"`);
  }

  return { status: errors.length ? 'failed' : warnings.length ? 'warnings' : 'passed', errors, warnings, chars, usesExperience };
}

module.exports = { validateDraft };
