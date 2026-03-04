const fetch = globalThis.fetch || require('node-fetch');

const BASE_URL = process.env.CANTON_JSON_API_BASE_URL || 'http://localhost:7575';
const PATIENT_PARTY = process.env.CANTON_PATIENT_PARTY;
const PHYSIO_PARTY = process.env.CANTON_PHYSIO_PARTY;
// API expects <packageId>:<module>:<entity> (two colons). Update if you rebuild the DAR.
const TEMPLATE_ID = process.env.CANTON_SESSIONLOG_TEMPLATE_ID || '532aa71ba2ab9ca3570c524feef11e0e6bce59bf904d1207f244dcf224c87f71:KrumpPhysio.Rehab:SessionLog';

function buildHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (process.env.CANTON_JWT) {
    headers.Authorization = `Bearer ${process.env.CANTON_JWT}`;
  }
  return headers;
}

async function logSessionToCanton({ score, round, angles, text }) {
  if (!PATIENT_PARTY || !PHYSIO_PARTY) {
    throw new Error(
      'CANTON_PATIENT_PARTY and CANTON_PHYSIO_PARTY must be set in .env (run from KrumpPhysio dir so dotenv loads it). See canton/CANTON.md.'
    );
  }

  const payload = {
    patient: PATIENT_PARTY,
    physio: PHYSIO_PARTY,
    round: String(round),
    score: typeof score === 'number' && Number.isFinite(score) ? score : 0,
    angles: typeof angles === 'string' ? angles : JSON.stringify(angles || []),
    notes: String(text || ''),
  };

  const res = await fetch(`${BASE_URL}/v1/create`, {
    method: 'POST',
    headers: buildHeaders(),
    body: JSON.stringify({
      templateId: TEMPLATE_ID,
      payload,
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Canton /v1/create failed: ${res.status} ${body}`);
  }

  return res.json();
}

module.exports = {
  logSessionToCanton,
};

