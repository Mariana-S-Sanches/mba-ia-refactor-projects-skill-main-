'use strict';

const db = require('./connection');
const { hashPasswordSync } = require('../services/authService');

function runSeed() {
  const usersCount = db.prepare('SELECT COUNT(*) AS c FROM users').get().c;
  if (usersCount === 0) {
    db.prepare(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    ).run('Leonan', 'leonan@fullcycle.com.br', hashPasswordSync('senha-inicial-troque'));
  }

  const coursesCount = db.prepare('SELECT COUNT(*) AS c FROM courses').get().c;
  if (coursesCount === 0) {
    const insert = db.prepare(
      'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
    );
    insert.run('Clean Architecture', 997.0, 1);
    insert.run('Docker', 497.0, 1);
  }
}

module.exports = { runSeed };
