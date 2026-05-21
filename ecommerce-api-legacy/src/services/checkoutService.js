'use strict';

const db = require('../db/connection');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const authService = require('./authService');
const paymentService = require('./paymentService');
const logger = require('../utils/logger');

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function maskCard(card) {
  if (!card) return '****';
  const last4 = card.slice(-4);
  return `**** **** **** ${last4}`;
}

/**
 * Faz o checkout em uma transação atômica.
 *
 *   1. Localiza o curso ativo
 *   2. Cria o usuário (se não existir)
 *   3. Cobra o cartão pelo paymentService
 *   4. Cria a matrícula
 *   5. Persiste o pagamento (status devolvido pelo gateway)
 *   6. Registra audit log
 *
 * Se qualquer passo lançar, a transação é revertida.
 */
function checkout({ name, email, password, courseId, card }) {
  const course = courseModel.findActiveById(courseId);
  if (!course) throw new HttpError(404, 'Curso não encontrado');

  const result = db.transaction(() => {
    let user = userModel.findByEmail(email);
    if (!user) {
      const newUserId = userModel.create({
        name,
        email,
        passHash: authService.hashPasswordSync(password),
      });
      user = { id: newUserId, name, email };
    }

    const chargeResult = paymentService.charge(card, course.price);
    if (chargeResult.status !== 'PAID') {
      throw new HttpError(400, 'Pagamento recusado');
    }

    const enrollmentId = enrollmentModel.create({ userId: user.id, courseId });
    paymentModel.create({
      enrollmentId,
      amount: chargeResult.amount,
      status: chargeResult.status,
    });
    paymentModel.logAudit(`Checkout curso ${courseId} por ${user.id}`);

    return { enrollmentId, userId: user.id, courseTitle: course.title };
  })();

  logger.info(
    { courseId, userId: result.userId, cardMask: maskCard(card) },
    'checkout.complete',
  );
  return result;
}

module.exports = { checkout, HttpError };
