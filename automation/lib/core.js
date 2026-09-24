'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const AUTOMATION_DIR = path.join(ROOT, 'automation');

function defaultDirs(mode) {
  const sub = mode === 'offline' ? 'offline-test' : '';
  return {
    output: path.join(AUTOMATION_DIR, 'output', sub),
    state: path.join(AUTOMATION_DIR, 'state', sub),
    logs: path.join(AUTOMATION_DIR, 'logs'),
  };
}

const isPlainObject = (v) => v != null && typeof v === 'object' && !Array.isArray(v);

// Objects merge key by key; arrays and scalars in the override replace the base value.
function deepMerge(base, override) {
  const out = { ...base };
  for (const [k, v] of Object.entries(override)) out[k] = isPlainObject(v) && isPlainObject(base[k]) ? deepMerge(base[k], v) : v;
  return out;
}

function loadConfig(file = path.join(AUTOMATION_DIR, 'config.json'), profile = null) {
  const { profiles = {}, ...base } = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!profile) return { ...base, profile: null };
  if (!profiles[profile]) throw new Error(`Unknown profile "${profile}". Defined in config.json: ${Object.keys(profiles).join(', ') || 'none'}`);
  return { ...deepMerge(base, profiles[profile]), profile };
}

// Same precedence as lib/_env.py: existing environment variables win over the repo-root .env.
function loadEnv(root = ROOT) {
  const values = {};
  const file = path.join(root, '.env');
  if (fs.existsSync(file)) {
    for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const m = line.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
      if (!m) continue;
      let v = m[2].trim();
      if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
      else v = v.replace(/\s+#.*$/, '');
      values[m[1]] = v;
    }
  }
  return (name) => process.env[name] || values[name] || '';
}

function zonedParts(date, timeZone) {
  const fmt = new Intl.DateTimeFormat('en-CA', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  });
  return Object.fromEntries(fmt.formatToParts(date).map((p) => [p.type, p.value]));
}

function localDate(date, timeZone) {
  const p = zonedParts(date, timeZone);
  return `${p.year}-${p.month}-${p.day}`;
}

function localHour(date, timeZone) {
  return Number(zonedParts(date, timeZone).hour);
}

function formatLocal(date, timeZone, label) {
  const p = zonedParts(date, timeZone);
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute} ${label}`;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    if (err.code === 'ENOENT') return fallback;
    throw new Error(`Cannot parse ${file}: ${err.message}`);
  }
}

function writeJson(file, data) {
  ensureDir(path.dirname(file));
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2) + '\n', 'utf8');
  fs.renameSync(tmp, file);
}

function writeText(file, text) {
  ensureDir(path.dirname(file));
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, text, 'utf8');
  fs.renameSync(tmp, file);
}

const LOCK_STALE_MS = 2 * 60 * 60 * 1000;

function acquireLock(stateDir, now = new Date()) {
  ensureDir(stateDir);
  const file = path.join(stateDir, 'run.lock');
  const existing = readJson(file, null);
  if (existing && now.getTime() - Date.parse(existing.startedAt) < LOCK_STALE_MS) {
    throw Object.assign(new Error(`Another run (pid ${existing.pid}) started at ${existing.startedAt} is still holding ${file}`), { code: 'LOCKED' });
  }
  writeJson(file, { pid: process.pid, startedAt: now.toISOString() });
  return () => { try { fs.unlinkSync(file); } catch { /* already gone */ } };
}

function createLogger(logDir, date, mode, quiet = false) {
  ensureDir(logDir);
  const file = path.join(logDir, `run_${date}${mode === 'offline' ? '_offline' : ''}.log`);
  const write = (level, msg) => {
    const line = `${new Date().toISOString()} [${level}] ${msg}`;
    fs.appendFileSync(file, line + '\n', 'utf8');
    if (!quiet) (level === 'ERROR' ? console.error : console.log)(line);
  };
  return {
    file,
    info: (m) => write('INFO', m),
    warn: (m) => write('WARN', m),
    error: (m) => write('ERROR', m),
  };
}

const round = (n, digits = 4) => Math.round(n * 10 ** digits) / 10 ** digits;
const clamp = (n, lo = 0, hi = 100) => Math.min(hi, Math.max(lo, n));

module.exports = {
  ROOT, AUTOMATION_DIR, defaultDirs, loadConfig, deepMerge, loadEnv,
  localDate, localHour, formatLocal, ensureDir, readJson, writeJson, writeText,
  acquireLock, createLogger, round, clamp,
};
