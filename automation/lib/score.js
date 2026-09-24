'use strict';

const { clamp, round } = require('./core');

// Audience size (reactions + velocity), discounted by how crowded the thread already is:
// a new comment under 2,000 existing comments is rarely seen, however big the post.
// With a follower count, the author's audience (20K -> 0, 1M+ -> 100, log scale) carries half the weight.
function reachScore(reactions, comments, ageHours, followers = null) {
  const rx = Math.max(reactions, 1);
  const size = clamp((100 * Math.log10(Math.max(rx, 100) / 100)) / Math.log10(20));
  const velocity = rx / Math.max(ageHours, 1);
  const speed = clamp((100 * Math.log10(1 + velocity)) / Math.log10(61));
  const audience = followers == null ? null : clamp((100 * Math.log10(Math.max(followers, 20000) / 20000)) / Math.log10(50));
  const raw = audience == null ? 0.6 * size + 0.4 * speed : 0.5 * audience + 0.3 * size + 0.2 * speed;
  const saturation = comments <= 60 ? 1 : Math.max(0.35, 1 - (0.65 * Math.log10(comments / 60)) / Math.log10(1000 / 60));
  return clamp(raw * saturation);
}

function recencyScore(ageHours, maxAgeHours) {
  return clamp(100 * (1 - ageHours / maxAgeHours));
}

// Visibility of one more comment: a few dozen comments is the sweet spot. Zero comments on a
// high-reaction post usually means inflated reactions; hundreds means the comment gets buried.
function competitionScore(comments, reactions) {
  if (comments >= 50 && comments / Math.max(reactions, 1) > 0.8) return 20;
  if (comments <= 2) return reactions >= 200 ? 25 : 60;
  if (comments <= 40) return 100;
  if (comments <= 150) return 100 - ((comments - 40) * 50) / 110;
  return clamp(50 - (40 * Math.log10(comments / 150)) / Math.log10(1000 / 150), 10, 50);
}

// For a thread already capped at maxComments: the emptier it is, the more visible a new comment.
function fewerCommentsScore(comments, maxComments) {
  return clamp(100 - (50 * comments) / Math.max(maxComments, 1));
}

function scorePost({ reactions, comments, ageHours, followers = null }, { relevance, insight }, weights, maxAgeHours, filters = {}) {
  const parts = {
    reach: reachScore(reactions, comments, ageHours, followers),
    recency: recencyScore(ageHours, maxAgeHours),
    relevance: clamp(relevance),
    competition: filters.maxComments != null ? fewerCommentsScore(comments, filters.maxComments) : competitionScore(comments, reactions),
    insight: clamp(insight),
  };
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  const total = Object.keys(weights).reduce((sum, k) => sum + parts[k] * weights[k], 0) / totalWeight;
  const rounded = Object.fromEntries(Object.entries(parts).map(([k, v]) => [k, Math.round(v)]));
  return { total: round(total, 1), ...rounded };
}

module.exports = { scorePost, reachScore, recencyScore, competitionScore, fewerCommentsScore };
