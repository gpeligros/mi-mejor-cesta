// frontend/api/stripe-checkout.js
// Crea una Stripe Checkout Session y devuelve la URL de pago

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }

  const stripeKey = process.env.STRIPE_SECRET_KEY;
  if (!stripeKey) {
    return res.status(500).json({ error: 'Stripe no configurado' });
  }

  const { planRequerido, userEmail, userId } = req.body;

  if (!planRequerido || !userId) {
    return res.status(400).json({ error: 'Faltan datos requeridos' });
  }

  const priceId = planRequerido === 'premium'
    ? process.env.STRIPE_PRICE_PREMIUM
    : process.env.STRIPE_PRICE_BASIC;

  if (!priceId) {
    return res.status(500).json({ error: 'Price ID no configurado' });
  }

  const appUrl = process.env.APP_URL || 'https://mi-mejor-cesta.vercel.app';

  try {
    const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${stripeKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'mode': 'subscription',
        'line_items[0][price]': priceId,
        'line_items[0][quantity]': '1',
        'success_url': `${appUrl}/?pago=ok&plan=${planRequerido}`,
        'cancel_url': `${appUrl}/?pago=cancelado`,
        'customer_email': userEmail || '',
        'metadata[user_id]': userId,
        'metadata[plan]': planRequerido,
        'locale': 'es',
        'allow_promotion_codes': 'true',
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      console.error('Stripe error:', err);
      return res.status(response.status).json({ error: err.error?.message || 'Error de Stripe' });
    }

    const session = await response.json();
    return res.status(200).json({ url: session.url });

  } catch (err) {
    console.error('Error en stripe-checkout:', err);
    return res.status(500).json({ error: 'Error interno del servidor' });
  }
}
