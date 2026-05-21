'use strict';

const userModel = require('../models/userModel');
const logger = require('../utils/logger');

function deleteUser(req, res, next) {
  try {
    const id = parseInt(req.params.id, 10);
    if (Number.isNaN(id) || id <= 0) {
      res.status(400).json({ error: 'ID inválido' });
      return;
    }
    const info = userModel.softDelete(id);
    if (info.changes === 0) {
      res.status(404).json({ error: 'Usuário não encontrado' });
      return;
    }
    logger.info({ id }, 'user.soft_deleted');
    res.status(200).json({ msg: 'Usuário desativado com sucesso' });
  } catch (err) {
    next(err);
  }
}

module.exports = { deleteUser };
