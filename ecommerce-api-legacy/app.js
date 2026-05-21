'use strict';

const express = require('express');
const config = require('./src/config');
const logger = require('./src/utils/logger');
const { initSchema } = require('./src/db/schema');
const { runSeed } = require('./src/db/seed');
const routes = require('./src/routes');
const errorHandler = require('./src/middlewares/errorHandler');

function createApp() {
  initSchema();
  runSeed();

  const app = express();
  app.use(express.json());
  app.use(routes);
  app.use(errorHandler);

  return app;
}

const app = createApp();

if (require.main === module) {
  app.listen(config.port, () => {
    logger.info({ port: config.port }, 'Frankenstein LMS rodando');
  });
}

module.exports = app;
