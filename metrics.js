#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const logFile = path.join(__dirname, 'logs', 'score-log.jsonl');

if (!fs.existsSync(logFile)) {
  console.error('No score log found at', logFile);
  process.exit(1);
}

const lines = fs.readFileSync(logFile, 'utf8').split('\n').filter(Boolean);

let count = 0;
let sumScore = 0;
let withScore = 0;

for (const line of lines) {
  try {
    const entry = JSON.parse(line);
    count += 1;
    if (typeof entry.score === 'number' && Number.isFinite(entry.score)) {
      sumScore += entry.score;
      withScore += 1;
    }
  } catch (_) {
    // skip malformed lines
  }
}

console.log('KrumpPhysio Metrics');
console.log('-------------------');
console.log('Total rounds scored:', count);
if (withScore > 0) {
  console.log('Average score (/10):', (sumScore / withScore).toFixed(2));
} else {
  console.log('Average score (/10): n/a (no parsable scores yet)');
}

