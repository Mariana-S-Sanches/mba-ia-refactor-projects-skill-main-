# Guidelines do Padrão MVC Alvo

Regras de organização para a Fase 3, **independentes de linguagem**. A skill deve adaptar a sintaxe ao idiom da stack detectada.

---

## 1. Responsabilidades de cada camada

### Model
- Representa **dados + regras de domínio sobre esses dados**.
- Conhece a estrutura da tabela/coleção.
- Expõe métodos como `is_overdue()`, `is_active()`, `apply_discount()`.
- **Não** importa nada do framework HTTP (`flask`, `express`, `request`).
- **Não** retorna `Response`/`jsonify`.

### View / Routes
- Define **mapping** HTTP → função do controller.
- Não contém regra de negócio.
- Não acessa banco.
- Em frameworks tipo Flask/Express, este é o arquivo que tem `app.route`/`router.get`. Em Rails é `config/routes.rb`.

### Controller
- Recebe a requisição, **delega** ao serviço/model, formata a resposta.
- Tem direito a: parsing de input, chamada de validação (idealmente delegada a um schema), construção da resposta.
- **Não** faz queries diretas (delega ao Model ou Service).
- **Não** contém regras de cálculo, decisão ou estado de domínio.

### Service (camada complementar quando necessário)
- Hospeda **regras de negócio que envolvem múltiplos models** ou integrações externas (email, SMS, gateway de pagamento, fila).
- Reutilizável fora do contexto HTTP (jobs, CLI, testes).
- Recebe dependências por injeção (não instancia coisas globais).

### Middleware
- Pipeline transversal: autenticação, CORS, logging, **tratamento centralizado de erros**, rate limit.

### Config
- Lê variáveis de ambiente em **um único lugar**.
- Fornece um objeto/dict imutável para o resto da aplicação.
- Tem um `.env.example` versionado para documentar as chaves.

---

## 2. Estrutura de pastas idiomática

### Python / Flask

```
src/
  config/
    __init__.py
    settings.py          # lê env vars; valida obrigatórias
  models/
    __init__.py
    produto.py
    usuario.py
    pedido.py
  controllers/
    __init__.py
    produto_controller.py
    usuario_controller.py
    pedido_controller.py
  views/                 # ou routes/ — escolha um e seja consistente
    __init__.py
    routes.py            # registro de blueprints
  services/
    __init__.py
    pedido_service.py    # checkout, recalculo, etc.
    notification_service.py
  middlewares/
    __init__.py
    error_handler.py
  utils/
    __init__.py
    logger.py
app.py                   # composition root: cria app, registra blueprints, error handlers
.env.example
requirements.txt
```

### Node.js / Express

```
src/
  config/
    index.js             # exporta config com getter de env
  models/
    User.js
    Course.js
    Enrollment.js
    Payment.js
  controllers/
    checkoutController.js
    reportController.js
    userController.js
  routes/
    checkoutRoutes.js
    reportRoutes.js
    userRoutes.js
    index.js             # registra todas as rotas
  services/
    paymentService.js
    enrollmentService.js
  middlewares/
    errorHandler.js
    requestLogger.js
  db/
    connection.js        # singleton de conexão tratado com cuidado
    schema.sql
  utils/
    logger.js
app.js                   # composition root
.env.example
package.json
```

### Ruby / Sinatra ou Rails-like
- Em Sinatra/Roda, espelhar a estrutura Express/Flask.
- Em Rails, manter a convenção `app/{models,controllers,views,services}` + `config/`.

### Outras stacks
- Java/Spring: `src/main/java/<pkg>/{controller,service,repository,model,config}` + `application.yml`.
- Go: `internal/{handler,service,repository,model}` + `cmd/api/main.go`.
- PHP/Laravel: `app/{Http/Controllers, Models, Services}` + `config/`.

A regra é: **separação por responsabilidade arquitetural primeiro, por feature depois** (se o projeto crescer).

---

## 3. Regras de dependência

```
routes ──► controllers ──► services ──► models ──► db
                ▲              ▲           ▲
                │              │           │
              utils       middlewares    config
```

**Setas só apontam para baixo.** Models não importam controllers. Controllers não conhecem rotas.

---

## 4. Padrões obrigatórios na refatoração

1. **Config externalizada.** Tudo que era literal vira `os.environ`/`process.env`/`ENV[]`. Em desenvolvimento, `.env` (no `.gitignore`). Em CI/Prod, secret manager.
2. **Queries parametrizadas.** Sem exceção. Para projetos que usam SQL puro, trocar `+` por `?`/`$1`. Para ORM, usar bound queries.
3. **Hashing de senha real.** `bcrypt`/`argon2`/`scrypt` da linguagem. Nunca MD5, SHA1, base64.
4. **Error handler centralizado.** Um único `@app.errorhandler(Exception)` (Flask) / `app.use((err, req, res, next) => ...)` (Express) que normaliza o payload de erro, oculta detalhes internos em produção e loga via logger estruturado.
5. **Logger estruturado.** Python: `logging.getLogger(__name__)`. Node: `pino`/`winston`. Nunca `print`/`console.log`.
6. **Validação por schema.** Marshmallow/Pydantic (Python), Joi/Zod (Node), `Validator` (Java/Spring).
7. **Eager loading para N+1.** SQLAlchemy: `joinedload`/`selectinload`. Sequelize: `include`. Prisma: `include`.
8. **Paginação default.** `?page=1&page_size=50` com cap de `page_size <= 100`.

---

## 5. O que NÃO fazer

- Renomear arquivos sem mover comportamento. (Pior cenário: cosmética que esconde dívida.)
- Quebrar contratos de endpoint existentes. Se um cliente espera `/produtos`, mantenha `/produtos`.
- Criar abstrações desnecessárias (Service para projeto com 4 endpoints CRUD, por exemplo, é overkill — controller-model basta).
- Misturar Models e DTOs. Se o framework já provê serialização (`marshmallow`, `pydantic`, `Sequelize.scope`), use.
- Esquecer `.env.example`. Sem ele, a refatoração não é reproduzível.

---

## 6. Critério de "MVC pronto"

A refatoração só está completa quando:

- [ ] Existe `config/` lendo de env vars.
- [ ] Existem `models/` sem nenhum import HTTP.
- [ ] Existem `controllers/` sem queries diretas (apenas chamadas a models/services).
- [ ] Existe `routes/` (ou `views/`) **só** com mapeamento HTTP → controller.
- [ ] Existe `middlewares/error_handler` ou equivalente.
- [ ] Existe entry point (`app.py`/`app.js`/equivalente) que apenas compõe as peças (composition root).
- [ ] A aplicação inicia.
- [ ] Os endpoints originais continuam respondendo.
