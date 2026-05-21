'use strict';

const db = require('../db/connection');

function create({ enrollmentId, amount, status }) {
  return db
    .prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)')
    .run(enrollmentId, amount, status).lastInsertRowid;
}

function logAudit(action) {
  db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(action);
}

module.exports = { create, logAudit };
