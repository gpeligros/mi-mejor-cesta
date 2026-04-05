// frontend/api/stripe-webhook.js
// Recibe eventos de Stripe y actualiza el plan en Supabase

export const config = {
  api: {
    bodyParser: false, // Stripe necesita el body raw para verificar la firma
  },
};

async function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

async function verificarFirmaStripe(rawBody, signature, secret) {
  // Verificación manual de la firma de Stripe (sin librería)
  const crypto = await import('crypto');
  
  const parts = signature.split(',');
  const timestamp = parts.find(p => p.startsWith('t=')).split('=')[1];
  const v1 = parts.find(p => p.startsWith('v1=')).split('=')[1];
  
  // Verificar que el timestamp no sea demasiado antiguo (5 minutos)
  const ahora = Math.floor(Date.now() / 1000);
  if (Math.abs(ahora - parseInt(timestamp)) > 300) {
    throw new Error('Timestamp expirado');
  }
  
  const payload = `${timestamp}.${rawBody}`;
  const hmac = crypto.default
    .createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');
  
  if (hmac !== v1) {
    throw new Error('Firma inválida');
  }
  
  return JSON.parse(rawBody);
}

async function actualizarPlanSupabase(userId, plan, stripeCustomerId, subscriptionId) {
  const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Supabase no configurado');
  }

  const res = await fetch(
    `${supabaseUrl}/rest/v1/profiles?id=eq.${userId}`,
    {
      method: 'PATCH',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({
        plan,
        stripe_id: stripeCustomerId,
        plan_desde: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    }
  );

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Error Supabase: ${err}`);
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    return res.status(500).json({ error: 'Webhook secret no configurado' });
  }

  const signature = req.headers['stripe-signature'];
  if (!signature) {
    return res.status(400).json({ error: 'Falta firma de Stripe' });
  }

  let evento;
  try {
    const rawBody = await getRawBody(req);
    evento = await verificarFirmaStripe(rawBody.toString(), signature, webhookSecret);
  } catch (err) {
    console.error('Error verificando webhook:', err.message);
    return res.status(400).json({ error: `Webhook inválido: ${err.message}` });
  }

  console.log(`Evento Stripe: ${evento.type}`);

  try {
    switch (evento.type) {

      // ── Pago completado → activar plan ─────────────────────
      case 'checkout.session.completed': {
        const session = evento.data.object;
        const userId = session.metadata?.user_id;
        const plan   = session.metadata?.plan;

        if (!userId || !plan) {
          console.error('Faltan metadata en checkout.session:', session.id);
          break;
        }

        await actualizarPlanSupabase(
          userId,
          plan,
          session.customer,
          session.subscription
        );
        console.log(`✅ Plan ${plan} activado para usuario ${userId}`);
        break;
      }

      // ── Suscripción renovada → mantener plan ───────────────
      case 'invoice.payment_succeeded': {
        const invoice = evento.data.object;
        const customerId = invoice.customer;

        // Buscar usuario por stripe_id
        const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

        const res2 = await fetch(
          `${supabaseUrl}/rest/v1/profiles?stripe_id=eq.${customerId}&select=id,plan`,
          {
            headers: {
              'apikey': supabaseKey,
              'Authorization': `Bearer ${supabaseKey}`,
            },
          }
        );
        const profiles = await res2.json();
        if (profiles && profiles[0]) {
          console.log(`✅ Renovación OK para ${profiles[0].id} — plan ${profiles[0].plan}`);
        }
        break;
      }

      // ── Suscripción cancelada → bajar a free ──────────────
      case 'customer.subscription.deleted': {
        const subscription = evento.data.object;
        const customerId = subscription.customer;

        const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

        // Buscar usuario por stripe_id
        const res3 = await fetch(
          `${supabaseUrl}/rest/v1/profiles?stripe_id=eq.${customerId}&select=id`,
          {
            headers: {
              'apikey': supabaseKey,
              'Authorization': `Bearer ${supabaseKey}`,
            },
          }
        );
        const profiles = await res3.json();
        if (profiles && profiles[0]) {
          await actualizarPlanSupabase(profiles[0].id, 'free', customerId, null);
          console.log(`⬇️ Plan bajado a free para ${profiles[0].id}`);
        }
        break;
      }

      // ── Pago fallido → notificar (sin bajar plan aún) ──────
      case 'invoice.payment_failed': {
        const invoice = evento.data.object;
        console.warn(`⚠️ Pago fallido para customer ${invoice.customer}`);
        break;
      }

      default:
        console.log(`Evento no manejado: ${evento.type}`);
    }

    return res.status(200).json({ received: true });

  } catch (err) {
    console.error('Error procesando evento:', err);
    return res.status(500).json({ error: 'Error procesando evento' });
  }
}
