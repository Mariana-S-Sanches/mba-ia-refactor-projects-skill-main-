'use strict';

const bcrypt = require('bcryptjs');

const ROUNDS = 12;

function hashPasswordSync(plain) {
  if (!plain || typeof plain !== 'string') {
    throw new Error('Senha inválida');
  }
  return bcrypt.hashSync(plain, ROUNDS);
}

function verifyPasswordSync(plain, hashed) {
  if (!plain || !hashed) return false;
  return bcrypt.compareSync(plain, hashed);
}

module.exports = { hashPasswordSync, verifyPasswordSync };
