'use strict';

const logger = require('../utils/logger');

// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, _req, res, _next) {
  if (err && typeof err.status === 'number') {
    res.status(err.status).json({ error: err.message });
    return;
  }
  logger.error({ err: err && err.message }, 'unhandled error');
  res.status(500).json({ error: 'Internal Server Error' });
};
