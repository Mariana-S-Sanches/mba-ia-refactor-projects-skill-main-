'use strict';

const db = require('../db/connection');

function findActiveById(id) {
  return db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(id);
}

function listAll() {
  return db.prepare('SELECT * FROM courses').all();
}

module.exports = { findActiveById, listAll };
