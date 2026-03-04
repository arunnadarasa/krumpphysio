#!/usr/bin/env node
/**
 * Build a development JWT for Daml JSON API (sandbox / Canton).
 * Use only for local dev; ledger must be running without strict auth.
 *
 * Required payload: https://daml.com/ledger-api with ledgerId, applicationId, actAs.
 * actAs must be the FULL party identifier (e.g. KrumpPhysioClinic::1220...52a).
 * Loads .env from project root when run from KrumpPhysio dir so CANTON_PHYSIO_PARTY is used.
 *
 * Usage: node canton/jwt-dev.js   (run from KrumpPhysio so .env is loaded)
 * Output: prints the JWT to stdout (set CANTON_JWT to this in .env).
 */

try {
  require('dotenv').config({ path: require('path').resolve(__dirname, '..', '.env') });
} catch (_) {}

const crypto = require('crypto');

const LEDGER_ID = process.env.CANTON_LEDGER_ID || 'sandbox';
const ACT_AS = process.env.CANTON_PHYSIO_PARTY || 'KrumpPhysioClinic';
const APP_ID = process.env.CANTON_APPLICATION_ID || 'KrumpPhysio';

function base64url(buf) {
  return Buffer.from(buf)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function sign(alg, key, data) {
  return crypto.createHmac('sha256', key).update(data).digest();
}

const header = { alg: 'HS256', typ: 'JWT' };
const payload = {
  'https://daml.com/ledger-api': {
    ledgerId: LEDGER_ID,
    applicationId: APP_ID,
    actAs: [ACT_AS],
  },
};

const secret = process.env.CANTON_JWT_SECRET || 'dev-secret-do-not-use-in-production';
const b64Header = base64url(JSON.stringify(header));
const b64Payload = base64url(JSON.stringify(payload));
const signature = base64url(sign('HS256', secret, `${b64Header}.${b64Payload}`));
const token = `${b64Header}.${b64Payload}.${signature}`;

console.log(token);
