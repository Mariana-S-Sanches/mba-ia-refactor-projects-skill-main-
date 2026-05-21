'use strict';

const db = require('../db/connection');

function health(_req, res) {
  try {
    db.prepare('SELECT 1').get();
    res.status(200).json({ status: 'ok', database: 'connected' });
  } catch (err) {
    res.status(503).json({ status: 'degraded', database: 'unreachable' });
  }
}

module.exports = { health };
