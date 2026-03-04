#!/usr/bin/env node

try {
  require('dotenv').config({ path: require('path').resolve(__dirname, '..', '.env') });
} catch (_) {}

const fetch = globalThis.fetch || require('node-fetch');

const BASE_URL = process.env.CANTON_JSON_API_BASE_URL || 'http://localhost:7575';
const PATIENT_PARTY = process.env.CANTON_PATIENT_PARTY;
const PHYSIO_PARTY = process.env.CANTON_PHYSIO_PARTY;
const TEMPLATE_ID = process.env.CANTON_SESSIONLOG_TEMPLATE_ID || '532aa71ba2ab9ca3570c524feef11e0e6bce59bf904d1207f244dcf224c87f71:KrumpPhysio.Rehab:SessionLog';

if (!PATIENT_PARTY || !PHYSIO_PARTY) {
  console.error('CANTON_PATIENT_PARTY and CANTON_PHYSIO_PARTY must be set');
  process.exit(1);
}

function buildHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (process.env.CANTON_JWT) {
    headers.Authorization = `Bearer ${process.env.CANTON_JWT}`;
  }
  return headers;
}

async function fetchSessionLogs() {
  const res = await fetch(`${BASE_URL}/v1/query`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({
      templateIds: [TEMPLATE_ID],
      query: {
        patient: PATIENT_PARTY,
        physio: PHYSIO_PARTY,
      },
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Canton /v1/query failed: ${res.status} ${body}`);
  }

  return res.json();
}

async function main() {
  try {
    const data = await fetchSessionLogs();
    const contracts = Array.isArray(data.result) ? data.result : [];

    let total = 0;
    let sumScore = 0;
    let withScore = 0;

    for (const c of contracts) {
      const payload = c.payload || {};
      total += 1;
      const score = typeof payload.score === 'number' ? payload.score : parseFloat(payload.score);
      if (Number.isFinite(score)) {
        sumScore += score;
        withScore += 1;
      }
    }

    console.log('KrumpPhysio Canton Metrics');
    console.log('--------------------------');
    console.log('Total sessions on-ledger:', total);
    if (withScore > 0) {
      console.log('Average score (/10):', (sumScore / withScore).toFixed(2));
    } else {
      console.log('Average score (/10): n/a (no numeric scores yet)');
    }
  } catch (err) {
    console.error('Failed to fetch Canton summary:', err.message || err);
    process.exit(1);
  }
}

main();

