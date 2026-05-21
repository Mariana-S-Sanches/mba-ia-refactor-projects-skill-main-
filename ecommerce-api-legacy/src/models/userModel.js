'use strict';

const db = require('../db/connection');

function findByEmail(email) {
  return db.prepare('SELECT id, name, email, pass FROM users WHERE email = ? AND deleted_at IS NULL').get(email);
}

function findById(id) {
  return db.prepare('SELECT id, name, email FROM users WHERE id = ? AND deleted_at IS NULL').get(id);
}

function create({ name, email, passHash }) {
  const info = db
    .prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)')
    .run(name, email, passHash);
  return info.lastInsertRowid;
}

function softDelete(id) {
  return db
    .prepare("UPDATE users SET deleted_at = datetime('now') WHERE id = ? AND deleted_at IS NULL")
    .run(id);
}

module.exports = { findByEmail, findById, create, softDelete };
