================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0 (+ SQLAlchemy 3.1.1 via Flask-SQLAlchemy)
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1, python-dotenv 1.0.0, requests 2.31.0
Domain:        Task Manager (tasks, users, categories, relatórios)
Architecture:  MVC parcial — possui pastas models/, routes/, services/, utils/, mas regra de negócio vive nas routes; services órfão; controllers ausentes
Source files:  10 files analyzed (app.py, database.py, seed.py, models/{__init__,task,user,category}.py, routes/{task,user,report}_routes.py, services/notification_service.py, utils/helpers.py)
DB tables:     tasks, users, categories (via SQLAlchemy)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   10 analyzed | ~700 lines of code
Date:    2026-05-20

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 4
Total: 18 findings

## Findings

### [CRITICAL] Hardcoded SECRET_KEY (AP-001)
- **File:** `app.py:13`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` versionado no source.
- **Impact:** Permite forjar assinatura de sessões/cookies Flask. Combinado com o "JWT" fake (AP-005), elimina qualquer noção de autenticação.
- **Recommendation:** Mover para `src/config/settings.py` lendo `os.environ["SECRET_KEY"]`. Adicionar `.env.example`.

### [CRITICAL] MD5 como hash de senha (AP-004)
- **File:** `models/user.py:29, 32`
- **Description:** `User.set_password` faz `hashlib.md5(pwd.encode()).hexdigest()`; `check_password` compara o MD5 igualmente. Sem salt, sem KDF, sem stretching.
- **Impact:** Considerado quebrado para senhas desde meados dos anos 2000. Rainbow tables resolvem qualquer hash em segundos.
- **Recommendation:** Trocar por `bcrypt`/`argon2`. Em `src/services/auth_service.py`, expor `hash_password` e `verify_password`. Coluna `password` continua armazenando o hash (bcrypt fits em VARCHAR(255)).

### [CRITICAL] SMTP credentials hardcoded (AP-001)
- **File:** `services/notification_service.py:7-10`
- **Description:** `email_host`, `email_user='taskmanager@gmail.com'`, `email_password='senha123'` no source.
- **Impact:** Conta de email compartilhada de fato pública. Atacante pode enviar phishing em nome do produto.
- **Recommendation:** Mover para env vars (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`). Carregar no `src/config/settings.py` e injetar no serviço.

### [CRITICAL] Senha exposta no `to_dict()` (AP-005)
- **File:** `models/user.py:21`
- **Description:** `User.to_dict()` inclui `'password': self.password`. Os endpoints `/users`, `/users/<id>` e `/login` retornam o hash em toda resposta.
- **Impact:** Mesmo após migração para bcrypt, o hash exposto facilita ataques offline. Em LGPD/GDPR é vazamento de dado de credencial.
- **Recommendation:** Criar `src/schemas/user_schema.py` com schema público (sem `password`). Substituir `user.to_dict()` por `UserPublicSchema().dump(user)` em todas as responses.

### [CRITICAL] Token "JWT" fake após login (AP-013, AP-001)
- **File:** `routes/user_routes.py:210`
- **Description:** `'token': 'fake-jwt-token-' + str(user.id)` retornado no login. Sem assinatura, sem expiração, sem claims.
- **Impact:** Qualquer cliente pode forjar token de qualquer usuário (`fake-jwt-token-42`). É teatro de autenticação.
- **Recommendation:** Implementar JWT real com `pyjwt`, claims (`sub`, `iat`, `exp`), assinado com `SECRET_KEY`. Criar `auth_service.create_token(user)` e `auth_service.verify_token(token)`. Adicionar middleware `auth_required` que valida no `Authorization: Bearer`.

### [HIGH] DEBUG=True com host 0.0.0.0 (AP-007)
- **File:** `app.py:34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` — debugger interativo do Flask exposto na rede.
- **Impact:** Em produção, qualquer exception entrega RCE via PIN do Werkzeug debugger.
- **Recommendation:** Ler `DEBUG` e `HOST` do `settings.py` (default `False` / `127.0.0.1`).

### [HIGH] Lógica "is_overdue" duplicada nas routes (AP-009)
- **File:** `routes/task_routes.py:30-39, 71-80, 171-180, 282-287`; `routes/report_routes.py:33-43, 132-135`
- **Description:** A mesma checagem `if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done','cancelled')` aparece copiada 5 vezes. O model `Task` já define `is_overdue()` mas ninguém chama.
- **Impact:** Mudança na regra (ex.: ignorar finais de semana) exige editar 5 arquivos. Bug garantido em inconsistência.
- **Recommendation:** Substituir todas as duplicatas por `task.is_overdue()`. Mover a montagem do dicionário com `overdue` para `src/schemas/task_schema.py` (campo computado).

### [HIGH] `bare except:` engolindo qualquer erro (AP-018)
- **File:** `routes/task_routes.py:62, 137, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 222`
- **Description:** Blocos como `try: ... except: return jsonify({'error': 'Erro interno'}), 500`. Captura inclusive `KeyboardInterrupt` e `SystemExit`.
- **Impact:** Esconde bugs reais; impede observabilidade; debug se torna tarefa de arqueologia.
- **Recommendation:** Centralizar em `src/middlewares/error_handler.py` registrando `@app.errorhandler(Exception)` e `@app.errorhandler(HttpError)`. Remover todos os `try/except` de cada handler.

### [HIGH] NotificationService órfão (código morto) (AP-013)
- **File:** `services/notification_service.py:1-49`
- **Description:** A classe inteira (`send_email`, `notify_task_assigned`, `notify_task_overdue`, `get_notifications`) nunca é instanciada nem importada por nenhuma route.
- **Impact:** Ilusão de modularidade — auditor casual pensa que existe notificação, e na verdade nada acontece quando uma task é atribuída. Bug invisível de negócio.
- **Recommendation:** Decidir o destino: (a) implementar de verdade (injetar no `task_service.assign()`) ou (b) remover o arquivo. Mantê-lo como está é pior que qualquer das opções.

### [HIGH] Routes acessam `db.session` diretamente (AP-008 brando)
- **File:** `routes/task_routes.py:147-152, 217-222, 232-236`; `routes/user_routes.py:81-89, 127-131, 144-150`; `routes/report_routes.py:184-187, 204-208, 218-222`
- **Description:** Toda criação/update/delete é feita inline com `db.session.add/commit/rollback` no handler HTTP.
- **Impact:** Sem service layer real, qualquer mudança transacional exige tocar todas as routes. Reuso fora de HTTP (jobs, CLI) impossível.
- **Recommendation:** Criar `src/services/{task,user,category}_service.py` com `create`, `update`, `delete`, `assign`. Routes (renomeadas para `views/`) chamam `controllers/` que chamam `services/`.

### [MEDIUM] N+1 em `GET /tasks` ao buscar `user` e `category` (AP-015)
- **File:** `routes/task_routes.py:42, 51`
- **Description:** Para cada task, `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`. Para 100 tasks, são 201 queries.
- **Impact:** Latência cresce linear; em produção, primeiro request já é lento.
- **Recommendation:** Usar `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`. Trocar montagem manual por `TaskSchema(many=True).dump(tasks)` com `user_name` / `category_name` derivados.

### [MEDIUM] N+1 em `/reports/summary` (AP-015)
- **File:** `routes/report_routes.py:56-58`
- **Description:** Loop `for u in users: Task.query.filter_by(user_id=u.id).all()`. Para cada usuário, uma query separada.
- **Impact:** Mesmo problema do anterior, magnificado quando a base de usuários cresce.
- **Recommendation:** Consolidar com um `SELECT user_id, status, COUNT(*) FROM tasks GROUP BY user_id, status` e processar em Python; ou usar `db.session.query(User).options(joinedload(User.tasks))`.

### [MEDIUM] Validação duplicada / `process_task_data` órfão (AP-017)
- **File:** `utils/helpers.py:57-108` vs `routes/task_routes.py:92-114, 167-184`
- **Description:** Existe `process_task_data` que faz toda a validação de uma task (título, status, prioridade, due_date, tags). Mas as routes refazem manualmente as mesmas checagens.
- **Impact:** Duplicação clássica; mudança em uma regra (limite de prioridade subir para 10) precisa ser feita em três lugares.
- **Recommendation:** Substituir as validações manuais por `TaskSchema().load(request.get_json())` (marshmallow já é dependência). Remover `process_task_data` ou movê-lo para o schema.

### [MEDIUM] CRUD de Category dentro de `report_routes.py` (AP-008 brando)
- **File:** `routes/report_routes.py:157-223`
- **Description:** Endpoints `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>` vivem no arquivo de relatórios.
- **Impact:** Confusão de responsabilidades; quem procura "category" não acha; futuras rotas de category serão duplicadas.
- **Recommendation:** Criar `src/views/category_routes.py` (ou `controllers/category_controller.py`). Mover os 4 endpoints. Manter no report apenas `summary` e `user_report`.

### [MEDIUM] Paginação ausente em `/tasks`, `/users`, `/reports/summary` (AP-016)
- **File:** `routes/task_routes.py:11-15` (list_all), `:240-271` (search), `:273-299` (stats); `routes/user_routes.py:10-25`; `routes/report_routes.py:12-101`
- **Description:** Listagens retornam tudo. `stats` carrega todas as tasks em memória só pra contar overdue.
- **Impact:** Em produção, primeiro request derruba.
- **Recommendation:** Aceitar `?page=1&page_size=50` (cap em 100) e aplicar `.paginate()` do Flask-SQLAlchemy. Para `stats`, usar `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` agregado.

### [LOW] `type(x) == list` em vez de `isinstance` (AP-026)
- **File:** `routes/task_routes.py:141, 210`; `utils/helpers.py:103`
- **Description:** Verificação direta de tipo.
- **Impact:** Falha em subclasses; viola Liskov.
- **Recommendation:** Substituir por `isinstance(tags, list)`. (Vai sumir naturalmente quando schema marshmallow assumir parsing.)

### [LOW] Imports não utilizados (AP-024)
- **File:** `routes/task_routes.py:7` (`json, os, sys, time`); `routes/report_routes.py:8` (`json`); `routes/user_routes.py:6` (`json`)
- **Description:** Imports sem uso.
- **Impact:** Ruído, sinal de copy-paste.
- **Recommendation:** Remover. Ferramenta (`ruff`, `flake8`) detectaria.

### [LOW] `print` para logging (AP-021)
- **File:** `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24`
- **Description:** Eventos importantes (task criada, user criado, erro de email) impressos com `print`.
- **Impact:** Sem nível, sem timestamp, sem correlação.
- **Recommendation:** `logging.getLogger(__name__)` em cada módulo; trocar por `log.info`/`log.error`.

### [LOW] `if/else` aninhado profundo em `Task.is_overdue` (AP-027)
- **File:** `models/task.py:50-60`
- **Description:** 3 níveis de if/else para retornar booleano.
- **Impact:** Legibilidade prejudicada; método com 10 linhas que deveria ter 3.
- **Recommendation:** `return bool(self.due_date and self.due_date < datetime.utcnow() and self.status not in ('done', 'cancelled'))`.

================================
Total: 18 findings
================================

Phase 2 complete. Total: 18 findings (CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 4)
Proceed with refactoring (Phase 3)? [y/n]
> y
