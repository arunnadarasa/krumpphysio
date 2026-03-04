const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });
const secret = process.env.STRIPE_SECRET_KEY;
if (!secret) {
  console.error(JSON.stringify({ error: 'STRIPE_SECRET_KEY not set in .env' }));
  process.exit(1);
}
const stripe = require('stripe')(secret);

async function createStripePaymentLink() {
  const { amount, currency, description } = parseArgs();

  try {
    const paymentLink = await stripe.paymentLinks.create({
      line_items: [{
        price_data: {
          currency: currency,
          unit_amount: amount,
          product_data: { name: description }
        },
        quantity: 1
      }]
    });
    console.log(JSON.stringify({
      url: paymentLink.url,
      id: paymentLink.id
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