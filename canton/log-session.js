#!/usr/bin/env node
/**
 * Log a single KrumpPhysio scoring session to the Canton ledger.
 * Used by the OpenClaw agent (e.g. from Telegram) when it decides to persist a score.
 *
 * Usage:
 *   node canton/log-session.js --score 9.7 --round 1 --angles '[{"joint":"left_shoulder","target":120,"observed":118}]' --notes "9.7/10\nFeedback: ..."
 *
 * All args optional except that at least score or notes should be provided for a useful log.
 * Loads .env from project root (KrumpPhysio) so CANTON_* and parties are set.
 */

const path = require('path');
try {
  require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });
} catch (_) {}

function parseArgs() {
  const args = process.argv.slice(2);
  const out = { score: null, round: '1', angles: [], notes: '' };
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];
    if ((arg === '--score' || arg === '-score') && next != null) {
      out.score = Number(args[++i]);
    } else if ((arg === '--round' || arg === '-round') && next != null) {
      out.round = String(args[++i]);
    } else if ((arg === '--angles' || arg === '-angles') && next != null) {
      try {
        out.angles = JSON.parse(args[++i]);
      } catch (_) {
        out.angles = [];
      }
    } else if ((arg === '--notes' || arg === '-notes') && next != null) {
      out.notes = String(args[++i]);
    }
  }
  return out;
}

async function main() {
  const { score, round, angles, notes } = parseArgs();
  const { logSessionToCanton } = require('./ledgerClient');
  await logSessionToCanton({
    score: score != null && Number.isFinite(score) ? score : 0,
    round,
    angles,
    text: notes,
  });
}

main().catch((err) => {
  console.error('log-session:', err.message || err);
  process.exit(1);
});
