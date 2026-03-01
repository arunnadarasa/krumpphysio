#!/usr/bin/env node
/**
 * KrumpFit: Score therapeutic movements using OpenClaw agent
 * Usage: node score.js '<angles_json>' <round>
 * Example: node score.js '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
 */

const { spawn } = require('child_process');
require('dotenv').config();

const angles = JSON.parse(process.argv[2]);
const round = process.argv[3];

const prompt = `Round ${round}: Score these angles:\n${angles.map(a => `${a.joint}: target ${a.target}°, observed ${a.observed}°`).join('\n')}\nGive score/10, feedback, Laban notation.`;

const child = spawn('openclaw', [
  'agent',
  '--agent', process.env.AGENT_LABEL || 'krumpbot-fit',
  '--message', prompt,
  '--json'
], { shell: true, stdio: 'pipe' });

let output = '';
child.stdout.on('data', d => output += d.toString());
child.stderr.on('data', d => console.error(d.toString()));

child.on('close', (code) => {
  if (code !== 0) {
    console.error(`Agent exited ${code}`);
    process.exit(1);
  }
  try {
    const parsed = JSON.parse(output);
    const text = parsed.response || parsed.text || parsed.message || output.trim();
    console.log(text);
  } catch (e) {
    console.log(output.trim());
  }
});
