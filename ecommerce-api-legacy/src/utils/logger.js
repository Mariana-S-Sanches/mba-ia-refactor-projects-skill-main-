'use strict';

const pino = require('pino');
const config = require('../config');

const logger = pino({
  level: config.logLevel,
  base: undefined, // não polui com pid/hostname
});

module.exports = logger;
