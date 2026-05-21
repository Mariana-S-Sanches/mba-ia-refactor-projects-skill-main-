# Playbook de Refatoração

Cada padrão abaixo é uma transformação **concreta**: o anti-pattern detectado na Fase 2, o jeito errado, o jeito certo, e o caminho de aplicação. Mantenha o **comportamento** do endpoint inalterado.

Os exemplos usam Python/Flask e Node.js/Express porque são as stacks dos projetos do desafio, mas o conceito é portável.

---

## TX-01 — Hardcoded credentials → Config + env vars

**Aplica em:** AP-001, AP-007 (DEBUG).

### Antes (Flask)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Antes (Express)
```javascript
// utils.js
const config = {
  dbPass: "senha_super_secreta_prod_123",
  paymentGatewayKey: "pk_live_1234567890abcdef",
  port: 3000
};
```

### Depois (Flask)
```python
# src/config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

def _required(key: str) -> str:
    v = os.environ.get(key)
    if not v:
        raise RuntimeError(f"Environment variable {key} is required")
    return v

class Settings:
    SECRET_KEY = _required("SECRET_KEY")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")

settings = Settings()
```

```python
# app.py (composition root)
from flask import Flask
from src.config.settings import settings

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```

### Depois (Express)
```javascript
// src/config/index.js
require('dotenv').config();

function required(key) {
  const v = process.env[key];
  if (!v) throw new Error(`Env var ${key} is required`);
  return v;
}

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  dbPass: required('DB_PASS'),
  paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
};
```

### `.env.example` (obrigatório)
```
SECRET_KEY=change-me
DEBUG=false
DATABASE_URL=sqlite:///app.db
PAYMENT_GATEWAY_KEY=pk_test_...
DB_PASS=change-me
```

---

## TX-02 — SQL Injection → Queries parametrizadas

**Aplica em:** AP-002.

### Antes
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" +
    nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"
)
```

### Depois
```python
# src/models/produto.py
def get_by_id(id: int) -> dict | None:
    db = get_db()
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    return dict(row) if row else None

# src/models/usuario.py
def create(nome: str, email: str, senha_hash: str, tipo: str = "cliente") -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cur.lastrowid
```

Em Node, `db.run("... WHERE id = ?", [id], callback)` já é parametrizado — a correção é eliminar concatenações remanescentes.

---

## TX-03 — Senha em plaintext / MD5 → bcrypt

**Aplica em:** AP-004.

### Antes (Python)
```python
# models.py
def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```

```python
# models/user.py (task-manager-api)
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```

### Antes (Node)
```javascript
// utils.js
function badCrypto(pwd) {
  let hash = "";
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}
```

### Depois (Python — bcrypt)
```python
# src/services/auth_service.py
import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

```python
# src/controllers/usuario_controller.py
def login():
    data = request.get_json() or {}
    user = usuario_model.get_by_email(data.get("email", ""))
    if not user or not verify_password(data.get("senha", ""), user["senha_hash"]):
        return jsonify({"erro": "Credenciais inválidas"}), 401
    return jsonify({"id": user["id"], "nome": user["nome"]}), 200
```

### Depois (Node — bcrypt)
```javascript
// src/services/authService.js
const bcrypt = require('bcrypt');

async function hashPassword(plain) {
  return bcrypt.hash(plain, 12);
}

async function verifyPassword(plain, hashed) {
  return bcrypt.compare(plain, hashed);
}

module.exports = { hashPassword, verifyPassword };
```

Adicione `bcrypt` (Python) ou `bcrypt` (Node) ao manifesto. **Migration:** ao detectar usuários com hash inseguro, force reset de senha no próximo login.

---

## TX-04 — God Class / God Module → Camadas separadas

**Aplica em:** AP-008.

### Antes
```python
# models.py — 350 linhas com queries, formatação e regra
def criar_pedido(usuario_id, itens):
    db = get_db(); cursor = db.cursor()
    total = 0
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        ...
```

### Depois
```python
# src/models/produto.py
class Produto:
    def __init__(self, row):
        self.id, self.nome, self.preco, self.estoque = row["id"], row["nome"], row["preco"], row["estoque"]
    @classmethod
    def get(cls, id): ...
    def has_stock(self, qty): return self.estoque >= qty
```

```python
# src/services/pedido_service.py
def criar_pedido(usuario_id: int, itens: list[dict]) -> dict:
    produtos = [Produto.get(i["produto_id"]) for i in itens]
    if any(p is None for p in produtos):
        raise ValueError("Produto não encontrado")
    for p, i in zip(produtos, itens):
        if not p.has_stock(i["quantidade"]):
            raise ValueError(f"Estoque insuficiente: {p.nome}")
    pedido_id = PedidoRepo.create(usuario_id, itens, produtos)
    notification_service.notify_created(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": sum(p.preco * i["quantidade"] for p, i in zip(produtos, itens))}
```

```python
# src/controllers/pedido_controller.py
def criar_pedido():
    data = request.get_json() or {}
    try:
        result = pedido_service.criar_pedido(data["usuario_id"], data["itens"])
        return jsonify({"dados": result, "sucesso": True}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
```

---

## TX-05 — Lógica no Controller → Service / Model

**Aplica em:** AP-009.

### Antes
```python
def create_task():
    data = request.get_json()
    if len(data.get("title", "")) < 3: return jsonify({"error": "Título muito curto"}), 400
    if data.get("priority", 3) < 1 or data["priority"] > 5: return jsonify({"error": "Prio inválida"}), 400
    ...
```

### Depois
```python
# src/schemas/task_schema.py  (marshmallow)
from marshmallow import Schema, fields, validate

class CreateTaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    status = fields.Str(load_default="pending", validate=validate.OneOf(["pending", "in_progress", "done", "cancelled"]))
```

```python
# src/controllers/task_controller.py
def create_task():
    data = CreateTaskSchema().load(request.get_json() or {})
    task = task_service.create(**data)
    return jsonify(task.to_dict()), 201
```

O controller fica com 2 linhas. A validação vive no schema. A regra de negócio (assignar, notificar) vive no service.

---

## TX-06 — Callback hell → async/await + transação

**Aplica em:** AP-010, AP-012, AP-019 (sqlite3 callback API).

### Antes (Express + sqlite3 callbacks)
```javascript
app.post('/api/checkout', (req, res) => {
  this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("Curso não encontrado");
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
      this.db.run("INSERT INTO enrollments ...", [...], function(err) {
        self.db.run("INSERT INTO payments ...", [...], function(err) {
          self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
            res.json({ msg: "Sucesso" });
          });
        });
      });
    });
  });
});
```

### Depois (Express + better-sqlite3 ou wrappers async, dentro de transação)
```javascript
// src/services/checkoutService.js
const db = require('../db/connection');

function checkout({ name, email, password, courseId, card }) {
  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(courseId);
  if (!course) throw new HttpError(404, 'Curso não encontrado');

  const tx = db.transaction((payload) => {
    let user = db.prepare('SELECT id FROM users WHERE email = ?').get(payload.email);
    if (!user) {
      const hash = require('./authService').hashPasswordSync(payload.password || randomPassword());
      const info = db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run(payload.name, payload.email, hash);
      user = { id: info.lastInsertRowid };
    }
    const enr = db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(user.id, payload.courseId);
    const status = paymentService.charge(payload.card, course.price);
    if (status !== 'PAID') throw new HttpError(400, 'Pagamento recusado');
    db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(enr.lastInsertRowid, course.price, status);
    db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(`Checkout curso ${payload.courseId} por ${user.id}`);
    return enr.lastInsertRowid;
  });

  return { enrollment_id: tx({ name, email, password, courseId, card }) };
}
```

```javascript
// src/controllers/checkoutController.js
async function checkout(req, res, next) {
  try {
    const result = checkoutService.checkout(req.body);
    res.status(200).json({ msg: 'Sucesso', ...result });
  } catch (err) { next(err); }
}
```

A transação garante atomicidade — substitui o AP-012 também.

---

## TX-07 — N+1 → Eager loading / query consolidada

**Aplica em:** AP-015.

### Antes (SQLAlchemy)
```python
@task_bp.route('/tasks')
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        user = User.query.get(t.user_id)
        cat = Category.query.get(t.category_id)
        result.append({...})  # 1 + N + N queries
```

### Depois
```python
from sqlalchemy.orm import joinedload

@task_bp.route('/tasks')
def get_tasks():
    tasks = (Task.query
                 .options(joinedload(Task.user), joinedload(Task.category))
                 .all())
    return jsonify([task_serializer.dump(t) for t in tasks]), 200
```

### Antes (raw SQL)
```python
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
```

### Depois
```python
pedido_ids = [p["id"] for p in pedidos]
itens = db.execute(
    f"SELECT * FROM itens_pedido WHERE pedido_id IN ({','.join('?' * len(pedido_ids))})",
    pedido_ids,
).fetchall()
itens_by_pedido = {}
for it in itens:
    itens_by_pedido.setdefault(it["pedido_id"], []).append(dict(it))
```

---

## TX-08 — Endpoints sem paginação → cursor/page padrão

**Aplica em:** AP-016.

### Antes
```python
@task_bp.route('/tasks')
def get_tasks():
    return jsonify([t.to_dict() for t in Task.query.all()]), 200
```

### Depois
```python
@task_bp.route('/tasks')
def get_tasks():
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('page_size', 50)), 1), 100)
    q = Task.query.options(joinedload(Task.user), joinedload(Task.category))
    paged = q.paginate(page=page, per_page=page_size, error_out=False)
    return jsonify({
        "data": [task_serializer.dump(t) for t in paged.items],
        "page": page,
        "page_size": page_size,
        "total": paged.total,
    }), 200
```

Use defaults conservadores (`page_size=50`) e cap (`<=100`). Mantenha compatibilidade do payload se o endpoint original retornava lista nua — encapsule em `data`.

---

## TX-09 — Error handling genérico → middleware centralizado

**Aplica em:** AP-018.

### Antes
```python
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

### Depois
```python
# src/middlewares/error_handler.py
import logging
log = logging.getLogger(__name__)

class HttpError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status; self.message = message

def register(app):
    @app.errorhandler(HttpError)
    def _http_error(e):
        return {"erro": e.message}, e.status

    @app.errorhandler(Exception)
    def _unhandled(e):
        log.exception("Unhandled error")
        return {"erro": "Internal Server Error"}, 500
```

```python
# src/controllers/produto_controller.py
def listar_produtos():
    produtos = produto_model.get_all()
    return jsonify({"dados": produtos, "sucesso": True}), 200
```

Em Express:
```javascript
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  req.log.error(err);
  if (err.status) return res.status(err.status).json({ erro: err.message });
  res.status(500).json({ erro: 'Internal Server Error' });
};
```

---

## TX-10 — Logging com print/console → logger estruturado

**Aplica em:** AP-021, AP-006 (remover PII dos logs).

### Antes
```python
print("Produto criado com ID: " + str(id))
print(f"Erro ao criar task: {str(e)}")
```
```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

### Depois (Python)
```python
# src/utils/logger.py
import logging, sys

def setup():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
```

```python
# src/controllers/produto_controller.py
import logging
log = logging.getLogger(__name__)
log.info("produto.created id=%s", produto_id)  # nunca PII direto
```

### Depois (Node)
```javascript
// src/utils/logger.js
const pino = require('pino');
module.exports = pino({ level: process.env.LOG_LEVEL || 'info' });
```

```javascript
log.info({ courseId: cid, userId: user.id }, 'checkout.start'); // nunca cc / cvv
```

---

## TX-11 — Estado global mutável → Singleton encapsulado + DI

**Aplica em:** AP-011.

### Antes
```javascript
// utils.js
let globalCache = {};
let totalRevenue = 0;
function logAndCache(key, data) { globalCache[key] = data; }
```

### Depois
```javascript
// src/services/cacheService.js
class CacheService {
  constructor() { this.store = new Map(); }
  set(key, value) { this.store.set(key, value); }
  get(key) { return this.store.get(key); }
  clear() { this.store.clear(); }
}
module.exports = new CacheService();  // singleton intencional, encapsulado
```

E injetar em quem precisar:
```javascript
// src/controllers/checkoutController.js
const cache = require('../services/cacheService');
cache.set(`last_checkout_${userId}`, courseTitle);
```

Em Python, encapsule conexão de banco em factory + `g` (Flask) ou em `app.teardown_appcontext`, nunca como `global`.

---

## TX-12 — DELETE sem CASCADE → soft delete ou FK CASCADE

**Aplica em:** AP-014.

### Antes
```javascript
app.delete('/api/users/:id', (req, res) => {
  this.db.run("DELETE FROM users WHERE id = ?", [id], () => {
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos");
  });
});
```

### Depois (opção A — soft delete recomendada para auditoria)
```javascript
// migration
ALTER TABLE users ADD COLUMN deleted_at DATETIME;
```

```javascript
// src/services/userService.js
function softDelete(id) {
  return db.prepare("UPDATE users SET deleted_at = datetime('now') WHERE id = ?").run(id);
}
```

E todas as queries de listagem passam a filtrar `WHERE deleted_at IS NULL`.

### Depois (opção B — schema com ON DELETE CASCADE)
```sql
CREATE TABLE enrollments (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  course_id INTEGER REFERENCES courses(id)
);
```

Garantir que ao detectar `AP-014`, a refatoração documente a escolha e atualize o schema.

---

## Como usar este playbook na Fase 3

1. Após confirmar a Fase 3, abra o relatório da Fase 2.
2. Para cada finding, encontre a TX correspondente (mapeamento abaixo).
3. Aplique a transformação **no menor escopo possível** — não reescreva código não tocado.
4. Mantenha os endpoints originais. Se um path mudar, anote.
5. Ao final, registre quais findings foram resolvidos e quais ficaram (sempre algum LOW pode ficar — está ok desde que CRITICAL/HIGH estejam zerados).

### Mapa rápido finding → transformação

| AP | TX |
|---|---|
| AP-001, AP-007 | TX-01 |
| AP-002, AP-003 | TX-02 |
| AP-004 | TX-03 |
| AP-005 | TX-01 (remove do response) + TX-09 |
| AP-006 | TX-10 |
| AP-008 | TX-04 |
| AP-009, AP-017 | TX-05 |
| AP-010 | TX-06 |
| AP-011 | TX-11 |
| AP-012 | TX-06 |
| AP-013 | TX-04 / TX-05 (mover para service real) |
| AP-014 | TX-12 |
| AP-015 | TX-07 |
| AP-016 | TX-08 |
| AP-018 | TX-09 |
| AP-019 | TX-06 (sqlite3) / atualizar dependência (`request` → `axios`/`fetch`) |
| AP-020 | mover para `config/` ou `models/<entidade>.STATUS_CHOICES` |
| AP-021 | TX-10 |
| AP-022, AP-023, AP-024, AP-025, AP-026, AP-027, AP-028 | limpeza local, sem TX dedicada — corrigir no arquivo afetado |
