'use strict';

const checkoutService = require('../services/checkoutService');
const { normalizeAndValidate } = require('../schemas/checkoutSchema');

function checkout(req, res, next) {
  try {
    const { value, error } = normalizeAndValidate(req.body || {});
    if (error) {
      res.status(400).json({ error: 'Payload inválido', details: error.details.map((d) => d.message) });
      return;
    }
    const result = checkoutService.checkout(value);
    res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
  } catch (err) {
    next(err);
  }
}

module.exports = { checkout };
