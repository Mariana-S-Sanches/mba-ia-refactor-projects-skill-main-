'use strict';

const db = require('../db/connection');

function create({ userId, courseId }) {
  return db
    .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
    .run(userId, courseId).lastInsertRowid;
}

module.exports = { create };
