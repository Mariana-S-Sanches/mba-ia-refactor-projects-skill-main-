'use strict';

const reportService = require('../services/reportService');

function financialReport(_req, res, next) {
  try {
    res.json(reportService.financialReport());
  } catch (err) {
    next(err);
  }
}

module.exports = { financialReport };
