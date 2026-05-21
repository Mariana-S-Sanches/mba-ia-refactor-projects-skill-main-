'use strict';

/**
 * Stub do gateway de pagamento. Em produção, isto faria uma chamada HTTPS
 * ao provedor (Stripe, MercadoPago, Pagar.me) usando `config.paymentGatewayKey`.
 *
 * IMPORTANTE: o número do cartão NUNCA é logado. Aqui só usamos o primeiro
 * dígito para decidir o resultado simulado (visa = PAID, outros = DENIED).
 */
function charge(card, amount) {
  if (!card || typeof card !== 'string') return 'DENIED';
  const firstDigit = card[0];
  const decision = firstDigit === '4' ? 'PAID' : 'DENIED';
  return { status: decision, amount };
}

module.exports = { charge };
