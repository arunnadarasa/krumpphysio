const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });
const secret = process.env.STRIPE_SECRET_KEY;
if (!secret) {
  console.error(JSON.stringify({ error: 'STRIPE_SECRET_KEY not set in .env' }));
  process.exit(1);
}
const stripe = require('stripe')(secret);

// #region agent log
// Minimal debug log so we can distinguish gateway/agent runs from manual runs.
try {
  // Use fetch-based logging per debug config (server provided by tooling).
  // This is fire-and-forget and will not affect Stripe behaviour.
  // eslint-disable-next-line no-undef
  fetch('http://127.0.0.1:7616/ingest/5f0664d2-0a08-4903-8919-61592e1268f8', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Debug-Session-Id': 'b06977'
    },
    body: JSON.stringify({
      sessionId: 'b06977',
      location: 'create-stripe-link.js:entry',
      message: 'Stripe payment link script invoked',
      data: {
        argv: process.argv,
        envNodeEnv: process.env.NODE_ENV || null
      },
      hypothesisId: 'H1',
      timestamp: Date.now()
    })
  }).catch(() => {});
} catch {
  // ignore logging errors
}
// #endregion

async function createStripePaymentLink() {
  const { amount, currency, description } = parseArgs();

  try {
    const tracingId = `KRUMPPHYSIO-${Date.now()}`;
    const paymentLink = await stripe.paymentLinks.create({
      line_items: [{
        price_data: {
          currency: currency,
          unit_amount: amount,
          product_data: {
            name: description,
            metadata: {
              service_name: 'krumpbot-fit',
              service_type: 'physiotherapy',
              tracing_id: tracingId,
              environment: process.env.NODE_ENV || 'sandbox'
            }
          }
        },
        quantity: 1
      }],
      metadata: {
        service_name: 'krumpbot-fit',
        service_type: 'physiotherapy',
        tracing_id: tracingId,
        environment: process.env.NODE_ENV || 'sandbox'
      }
    });
    console.log(JSON.stringify({
      url: paymentLink.url,
      id: paymentLink.id,
      tracingId
    }));
  } catch (error) {
    console.error('Stripe API error:', error.message);
    process.exit(1);
  }
}

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].replace('--', '');
      params[key] = args[i + 1];
      i++;
    }
  }

  return {
    amount: parseInt(params.price || params.amount),
    currency: params.currency || 'usd',
    description: params.description
  };
}

createStripePaymentLink();