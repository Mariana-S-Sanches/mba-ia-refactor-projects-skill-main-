"""Script para popular o banco com dados iniciais (agora com bcrypt)."""
from __future__ import annotations

from datetime import datetime, timedelta

from app import app
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.auth_service import hash_password


def seed_data() -> None:
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = [
            User(name="João Silva", email="joao@email.com", password=hash_password("1234"), role="admin"),
            User(name="Maria Santos", email="maria@email.com", password=hash_password("abcd"), role="user"),
            User(name="Pedro Oliveira", email="pedro@email.com", password=hash_password("pass"), role="manager"),
        ]
        db.session.add_all(users)
        db.session.commit()

        categories = [
            Category(name="Backend", description="Tarefas de backend", color="#3498db"),
            Category(name="Frontend", description="Tarefas de frontend", color="#2ecc71"),
            Category(name="DevOps", description="Tarefas de infraestrutura", color="#e74c3c"),
            Category(name="Bug", description="Correção de bugs", color="#e67e22"),
        ]
        db.session.add_all(categories)
        db.session.commit()

        u1, u2, u3 = users
        c_back, c_front, c_devops, c_bug = categories

        tasks_data = [
            ("Implementar autenticação JWT", "Adicionar autenticação real com JWT", "pending", 1, u1.id, c_back.id, datetime.utcnow() - timedelta(days=3), None),
            ("Criar tela de login", "Tela de login responsiva", "in_progress", 2, u2.id, c_front.id, datetime.utcnow() + timedelta(days=5), None),
            ("Configurar CI/CD", "Pipeline com GitHub Actions", "done", 2, u3.id, c_devops.id, None, "devops,ci,github"),
            ("Corrigir bug no filtro de busca", "Filtro não funciona com caracteres especiais", "pending", 1, u1.id, c_bug.id, datetime.utcnow() - timedelta(days=1), None),
            ("Adicionar paginação na API", "Endpoints retornam todos os registros", "pending", 3, u1.id, c_back.id, datetime.utcnow() + timedelta(days=10), None),
            ("Escrever testes unitários", "Cobertura mínima de 80%", "pending", 2, u2.id, c_back.id, None, None),
            ("Documentar API com Swagger", "Gerar documentação automática", "cancelled", 4, u3.id, c_back.id, None, None),
            ("Refatorar models", "Melhorar organização dos models", "in_progress", 3, u2.id, c_back.id, None, "refactor,tech-debt"),
            ("Configurar monitoramento", "Prometheus + Grafana", "pending", 4, u3.id, c_devops.id, datetime.utcnow() + timedelta(days=20), None),
            ("Melhorar validações de input", "Usar marshmallow ou pydantic", "pending", 3, u1.id, c_back.id, None, "improvement,validation"),
        ]
        for title, desc, status, priority, uid, cid, due, tags in tasks_data:
            db.session.add(
                Task(
                    title=title,
                    description=desc,
                    status=status,
                    priority=priority,
                    user_id=uid,
                    category_id=cid,
                    due_date=due,
                    tags=tags,
                )
            )

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == "__main__":
    seed_data()
