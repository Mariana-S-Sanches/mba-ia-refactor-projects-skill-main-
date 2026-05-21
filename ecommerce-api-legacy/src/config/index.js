'use strict';

require('dotenv').config();

function required(key) {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Environment variable ${key} is required`);
  }
  return value;
}

function optional(key, fallback) {
  return process.env[key] || fallback;
}

module.exports = {
  port: parseInt(optional('PORT', '3000'), 10),
  logLevel: optional('LOG_LEVEL', 'info'),
  paymentGatewayKey: optional('PAYMENT_GATEWAY_KEY', 'pk_test_local'),
  databasePath: optional('DATABASE_PATH', ':memory:'),
};
