#!/usr/bin/env node
/**
 * KrumpPhysio: Score therapeutic movements using OpenClaw agent
 * Usage: node score.js '<angles_json>' <round>
 * Example: node score.js '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
 */

require('dotenv').config();

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
let cantonClient = null;
try {
  cantonClient = require('./canton/ledgerClient');
} catch (_) {
  // Canton integration is optional; ignore if client not present
}

const angles = JSON.parse(process.argv[2]);
const round = process.argv[3];

const prompt = `Round ${round}: Score these angles:\n${angles.map(a => `${a.joint}: target ${a.target}°, observed ${a.observed}°`).join('\n')}\nGive score/10, feedback, Laban notation.`;

const child = spawn('openclaw', [
  'agent',
  '--agent', process.env.AGENT_LABEL || 'krumpbot-fit',
  '--message', prompt,
  '--json'
], { stdio: 'pipe' });

let output = '';
child.stdout.on('data', d => output += d.toString());
child.stderr.on('data', d => console.error(d.toString()));

child.on('close', (code) => {
  if (code !== 0) {
    console.error(`Agent exited ${code}`);
    process.exit(1);
  }

  let text = output.trim();
  try {
    const parsed = JSON.parse(output);
    text = parsed?.result?.payloads?.[0]?.text ?? parsed.response ?? parsed.text ?? parsed.message ?? text;
  } catch (_) {
    // leave text as-is if JSON parse fails
  }

  // Best-effort score extraction: look for first "<number>/10" anywhere (e.g. "Score: 9.7/10" in body)
  let score = null;
  const match = text.match(/(\d+(?:\.\d+)?)\s*\/\s*10/);
  if (match) {
    score = Number(match[1]);
  }

  // Append JSONL metrics entry
  try {
    const logDir = path.join(__dirname, 'logs');
    const logFile = path.join(logDir, 'score-log.jsonl');
    fs.mkdirSync(logDir, { recursive: true });
    const entry = {
      ts: new Date().toISOString(),
      round,
      angles,
      score,
      raw: text
    };
    fs.appendFileSync(logFile, JSON.stringify(entry) + '\n');
  } catch (err) {
    console.error('Warning: failed to write score log:', err.message);
  }

  // Optional: also persist to Canton ledger if configured
  if (cantonClient && process.env.CANTON_ENABLE === 'true') {
    cantonClient
      .logSessionToCanton({
        score,
        round,
        angles,
        text,
      })
      .catch((err) => {
        console.error('Warning: failed to log session to Canton:', err.message || err);
      });
  }

  console.log(text);
});
