'use strict';

// Usa o driver SQLite nativo do Node 22+ (síncrono, sem dependência de build).
// API equivalente à do better-sqlite3: prepare/get/run/all, transaction.
const { DatabaseSync } = require('node:sqlite');
const config = require('../config');

const db = new DatabaseSync(config.databasePath);
db.exec('PRAGMA foreign_keys = ON');

// Helper transaction(fn) compatível com better-sqlite3.
db.transaction = function transactionWrapper(fn) {
  return (...args) => {
    db.exec('BEGIN');
    try {
      const result = fn(...args);
      db.exec('COMMIT');
      return result;
    } catch (err) {
      db.exec('ROLLBACK');
      throw err;
    }
  };
};

module.exports = db;
