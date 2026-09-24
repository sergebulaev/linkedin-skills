'use strict';

// The only file in automation/ that talks to Publora. Used exclusively by publish-cli.js's
// "publish" command (never by run-daily.js, never by tests, which always inject a fake
// publishOne instead of importing this module).

async function createLinkedInComment({ postedId, message, platformId, apiKey, fetchImpl = fetch, timeoutMs = 60000 }) {
  const res = await fetchImpl('https://api.publora.com/api/v1/linkedin-comments', {
    method: 'POST',
    headers: { 'x-publora-key': apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ postedId, message, platformId }),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await res.text();
  let body;
  try { body = text ? JSON.parse(text) : {}; } catch { body = { raw: text.slice(0, 500) }; }
  if (res.status < 200 || res.status >= 300) {
    const err = new Error(`Publora HTTP ${res.status}: ${JSON.stringify(body).slice(0, 300)}`);
    err.httpStatus = res.status;
    err.body = body;
    throw err;
  }
  return { httpStatus: res.status, body };
}

// Returns a publishOne(item) function bound to one API key/platform. Tries the activity URN
// first; if Publora 404s on it, retries once with the post's share/ugcPost URN (some posts'
// canonical commentable URN differs from the activity id in the URL). Any other error propagates.
function makePublishOne({ apiKey, platformId, fetchImpl }) {
  if (!apiKey || !platformId) throw new Error('makePublishOne: apiKey and platformId are both required');
  return async function publishOne(item) {
    const attempts = [];
    try {
      const res = await createLinkedInComment({ postedId: item.postedId, message: item.message, platformId, apiKey, fetchImpl });
      attempts.push({ postedId: item.postedId, httpStatus: res.httpStatus });
      return { attempts, ...res };
    } catch (err) {
      attempts.push({ postedId: item.postedId, httpStatus: err.httpStatus });
      if (err.httpStatus === 404 && item.fallbackPostedId) {
        const res2 = await createLinkedInComment({ postedId: item.fallbackPostedId, message: item.message, platformId, apiKey, fetchImpl });
        attempts.push({ postedId: item.fallbackPostedId, httpStatus: res2.httpStatus });
        return { attempts, ...res2 };
      }
      throw err;
    }
  };
}

module.exports = { createLinkedInComment, makePublishOne };
