'use strict';

function fmtUsd(n) {
  return n == null ? 'n/a' : `$${Number(n).toFixed(3)}`;
}

function card(c) {
  const v = c.validation || { status: 'not_drafted', errors: [], warnings: [] };
  const checks = v.status === 'passed' ? 'passed'
    : v.status === 'warnings' ? `passed with warnings (${v.warnings.join('; ')})`
      : v.status === 'failed' ? `FAILED (${v.errors.join('; ')})` : 'not drafted yet';
  const lines = [
    `## ${c.rank}. ${c.author.name} | score ${c.scores.total}`,
    '',
    `- **LinkedIn URL:** ${c.url}`,
    `- **Author headline:** ${c.author.headline || 'n/a'}`,
    `- **Post age:** ${Math.round(c.ageHours)}h (posted ${c.postedAtLocal})`,
    `- **Reactions:** ${c.reactions} | **Comments:** ${c.comments} (as of ${c.engagementAsOfLocal})`,
    `- **Reach assessment:** ${c.reachAssessment || 'pending model review'}`,
    `- **Relevance score:** ${c.relevanceScore}/100 (keyword match ${c.heuristicRelevance}${c.modelRelevance != null ? `, model ${c.modelRelevance}` : ''}; topics: ${c.matchedTopics.join(', ') || 'none'})`,
    `- **Score breakdown:** reach ${c.scores.reach} | recency ${c.scores.recency} | relevance ${c.scores.relevance} | competition ${c.scores.competition} | insight ${c.scores.insight}`,
    `- **Why it is worth commenting on:** ${c.reason || 'pending model review'}`,
    `- **Technical angle:** ${c.angle || 'pending model review'}`,
  ];
  if (c.flags.length) lines.push(`- **Flags:** ${c.flags.join(', ')}`);
  if (c.injectionSuspected) lines.push('- **Warning:** text in this post or its comments appeared to address an AI agent. It was treated as data and kept out of the draft.');
  lines.push('');
  if (c.draft) {
    lines.push(`**Comment draft** (${c.draftChars} chars, uses your experience: ${c.usesExperience ? 'yes' : 'no'}, checks: ${checks}):`, '', '```text', c.draft, '```');
  } else {
    lines.push('**Comment draft:** not available yet (run again to retry drafting).');
  }
  lines.push('');
  return lines.join('\n');
}

function renderDatedMarkdown(r) {
  const s = r.summary;
  const out = [
    `# LinkedIn comment candidates, ${r.date}`,
    '',
    `Generated ${r.generatedAtLocal}. Draft-only: nothing was posted, liked, followed or published. Review each draft and post it yourself.`,
    '',
    '## Run summary',
    '',
    `- **Status:** ${r.status}${r.mode === 'offline' ? ' (offline test data)' : ''}`,
    `- **Posts in the ${r.thresholds.maxAgeHours}h window:** ${s.postsInWindow} | **with ${r.thresholds.minReactions}+ reactions:** ${s.qualifiedByReactions} | **passed filters:** ${s.passedFilters} | **drafted:** ${s.drafted} | **final:** ${s.final}`,
  ];
  if (s.shortfall) out.push(`- **Shortfall:** ${s.shortfall}`);
  out.push(
    `- **Discovery:** ${r.discovery.ran ? 'ran' : `skipped (${r.discovery.stopReason})`}${r.discovery.steps.length ? `; budget adjustments: ${r.discovery.steps.join(', ')}` : ''}`,
    `- **Apify cost this run:** estimated ${fmtUsd(r.cost.runEstimatedUsd)}, charged ${fmtUsd(r.cost.runActualUsd)} across ${r.cost.apifyCalls} actor runs`,
    `- **Apify cycle:** automation spent ${fmtUsd(r.cost.automationSpentThisCycleUsd)}; account ${fmtUsd(r.cost.accountUsedUsd)} of ${fmtUsd(r.cost.accountLimitUsd)} used; cycle ends ${r.cost.cycleEnd || 'n/a'}`,
    `- **Claude drafting:** ${r.cost.claudeCalls} call(s), reported cost ${fmtUsd(r.cost.claudeReportedCostUsd)} (plan usage if you are on a Claude subscription)`,
    `- **Ranking:** reach ${r.weights.reach}% (reactions and velocity, discounted for crowded threads), recency ${r.weights.recency}%, relevance ${r.weights.relevance}%, competition ${r.weights.competition}%, insight ${r.weights.insight}%`,
  );
  const excluded = Object.entries(s.excludedByReason);
  if (excluded.length) out.push(`- **Excluded by filters:** ${excluded.map(([k, v]) => `${k} ${v}`).join(', ')}`);
  if (s.modelExcluded.length) {
    out.push('- **Excluded after reading the post:**');
    for (const m of s.modelExcluded) out.push(`  - ${m.author}: ${m.reason} (${m.url})`);
  }
  if (s.validationDropped.length) {
    out.push('- **Dropped because the draft failed checks twice:**');
    for (const m of s.validationDropped) out.push(`  - ${m.author}: ${m.errors.join('; ')}`);
  }
  out.push('', '## Candidates', '');
  if (!r.candidates.length) out.push('No candidates today.', '');
  for (const c of r.candidates) out.push(card(c));
  return out.join('\n');
}

function renderLatestMarkdown(r) {
  const out = [
    `# Today's LinkedIn comment candidates (${r.date})`,
    '',
    `Generated ${r.generatedAtLocal}. ${r.candidates.length} candidate${r.candidates.length === 1 ? '' : 's'}. Draft-only: review and post manually.`,
  ];
  if (r.summary.shortfall) out.push('', `Note: ${r.summary.shortfall}`);
  out.push('');
  for (const c of r.candidates) out.push(card(c));
  return out.join('\n');
}

function queueItemCard(item) {
  const lines = [
    `## ${item.n}. ${item.author} | ${item.status}`,
    '',
    `- **Post URL:** ${item.url}`,
    `- **Reactions:** ${item.reactions} | **Comments:** ${item.comments}`,
    `- **postedId:** ${item.postedId}${item.fallbackPostedId ? ` (fallback: ${item.fallbackPostedId})` : ''}`,
  ];
  if (item.approvedAt) lines.push(`- **Approved:** ${item.approvedAt}${item.approvedNote ? ` (${item.approvedNote})` : ''}`);
  if (item.publishedAt) lines.push(`- **Published:** ${item.publishedAt}`);
  if (item.status === 'FAILED' && item.publoraResult) lines.push(`- **Error:** ${item.publoraResult.error}`);
  lines.push('', `**Comment** (${item.chars} chars):`, '', '```text', item.message, '```', '');
  return lines.join('\n');
}

function renderQueueMarkdown(q) {
  const counts = q.items.reduce((m, i) => ({ ...m, [i.status]: (m[i.status] || 0) + 1 }), {});
  const out = [
    `# Publish queue, ${q.date}`,
    '',
    `Updated ${q.updatedAt}. ${q.items.length} item(s): ${Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(', ')}.`,
    '',
    'Nothing here is published by viewing this file. An item moves to PUBLISHED only after an',
    'explicit approve, then an explicit publish, naming that item or "all".',
    '',
  ];
  for (const item of q.items) out.push(queueItemCard(item));
  return out.join('\n');
}

module.exports = { renderDatedMarkdown, renderLatestMarkdown, renderQueueMarkdown };
