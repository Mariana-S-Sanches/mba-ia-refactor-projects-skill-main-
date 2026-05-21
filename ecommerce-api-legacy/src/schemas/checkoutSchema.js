'use strict';

const Joi = require('joi');

/**
 * Schema do payload do checkout.
 *
 * Para preservar compatibilidade com clientes antigos, aceitamos tanto o
 * contrato novo (`name/email/password/courseId/card`) quanto o legado
 * (`usr/eml/pwd/c_id/card`). O middleware normaliza para o nome novo.
 */
const checkoutSchema = Joi.object({
  name: Joi.string().min(2).max(120).required(),
  email: Joi.string().email().required(),
  password: Joi.string().min(6).required(),
  courseId: Joi.number().integer().positive().required(),
  card: Joi.string().pattern(/^[0-9]{12,19}$/).required(),
});

function normalizeAndValidate(body) {
  const candidate = {
    name: body.name ?? body.usr,
    email: body.email ?? body.eml,
    password: body.password ?? body.pwd,
    courseId: body.courseId ?? body.c_id,
    card: body.card,
  };
  return checkoutSchema.validate(candidate, { abortEarly: false });
}

module.exports = { normalizeAndValidate };
