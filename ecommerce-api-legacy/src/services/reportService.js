'use strict';

const db = require('../db/connection');

/**
 * Relatório financeiro consolidado SEM N+1.
 *
 * Duas queries:
 *  1. Receita por curso (JOIN agregado)
 *  2. Lista de pagamentos por curso (uma só, agrupada por aplicação)
 */
function financialReport() {
  const revenueByCourse = db
    .prepare(
      `
      SELECT
        c.id AS courseId,
        c.title AS course,
        COALESCE(SUM(CASE WHEN p.status = 'PAID' THEN p.amount ELSE 0 END), 0) AS revenue
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN payments    p ON p.enrollment_id = e.id
      GROUP BY c.id, c.title
      ORDER BY c.id
    `,
    )
    .all();

  const students = db
    .prepare(
      `
      SELECT c.id AS courseId,
             u.name AS student,
             COALESCE(p.amount, 0) AS paid
      FROM courses c
      JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u  ON u.id = e.user_id AND u.deleted_at IS NULL
      LEFT JOIN payments p ON p.enrollment_id = e.id
    `,
    )
    .all();

  const studentsByCourse = students.reduce((acc, s) => {
    if (!acc[s.courseId]) acc[s.courseId] = [];
    acc[s.courseId].push({ student: s.student || 'Unknown', paid: s.paid });
    return acc;
  }, {});

  return revenueByCourse.map((row) => ({
    course: row.course,
    revenue: row.revenue,
    students: studentsByCourse[row.courseId] || [],
  }));
}

module.exports = { financialReport };
