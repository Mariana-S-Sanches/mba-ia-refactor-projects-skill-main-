================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js 18+)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API com fluxo de checkout (users, courses, enrollments, payments, audit_logs)
Architecture:  God Class — `AppManager` concentra DB, rotas e regra de negócio; estado global em `utils.js`
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   3 analyzed | ~170 lines of code
Date:    2026-05-20

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 3
Total: 17 findings

## Findings

### [CRITICAL] Hardcoded credentials e gateway key (AP-001)
- **File:** `src/utils.js:1-7`
- **Description:** `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"` versionados no source.
- **Impact:** A primeira clonagem do repositório vaza credenciais de produção e a chave do gateway de pagamento.
- **Recommendation:** Mover para `src/config/index.js` lendo de `process.env`. Adicionar `.env.example` documentando as chaves e bloquear `.env` no `.gitignore`.

### [CRITICAL] "Hash" de senha não criptográfico (AP-004, AP-019)
- **File:** `src/utils.js:17-23`
- **Description:** `badCrypto(pwd)` itera 10.000 vezes concatenando `Buffer.from(pwd).toString('base64')` e retorna apenas os 10 primeiros caracteres. Não é hash criptográfico — é base64 truncado.
- **Impact:** Senhas reversíveis em milissegundos. Equivalente a armazenar em plaintext.
- **Recommendation:** Substituir por `bcrypt` (`bcrypt.hash(pwd, 12)` / `bcrypt.compare`). Atualizar `package.json` para incluir `bcrypt@^5`.

### [CRITICAL] Número de cartão e key logados no console (AP-006)
- **File:** `src/AppManager.js:45`
- **Description:** `console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)` grava PAN + chave do gateway no stdout.
- **Impact:** Falha PCI-DSS imediata. Qualquer agregador de logs (CloudWatch, Datadog, ELK) coleta dados de cartão em texto puro.
- **Recommendation:** Remover o log. Em diagnóstico, logar apenas BIN (`cc.slice(0, 6)`) e os 4 últimos dígitos (`cc.slice(-4)`). Nunca logar a key do gateway.

### [CRITICAL] Senha em plaintext no seed inicial (AP-004)
- **File:** `src/AppManager.js:18`
- **Description:** `INSERT INTO users (name, email, pass) VALUES ('Leonan', '...', '123')` insere senha "123" sem hash.
- **Impact:** Conta admin do seed comprometida. Combinada com `badCrypto`, indica que não há nenhum controle de credenciais.
- **Recommendation:** Migrar para seed parametrizado que aplica `bcrypt.hashSync` antes do INSERT. Promover seed a script separado (`src/db/seed.js`).

### [CRITICAL] Senha default "123456" para novos usuários (AP-004)
- **File:** `src/AppManager.js:68`
- **Description:** Em `/api/checkout`, se o corpo não trouxer `pwd`, o sistema cria usuário com `badCrypto("123456")`.
- **Impact:** Qualquer conta criada via checkout sem senha vira adivinhavel. Combina vetor de senha fraca com hashing quebrado.
- **Recommendation:** Tornar `password` obrigatória no schema do checkout. Se ausente, retornar 400; nunca silenciosamente atribuir senha conhecida.

### [HIGH] God Class `AppManager` mistura DB + rotas + lógica (AP-008)
- **File:** `src/AppManager.js:1-141`
- **Description:** Uma única classe abre conexão SQLite no construtor, faz seed dentro de `initDb()`, define todas as rotas em `setupRoutes(app)` com handlers contendo regra de negócio (cálculo de status de pagamento, fluxo de checkout, cálculo de receita).
- **Impact:** Cada mudança de qualquer parte (rota nova, troca de banco, novo cálculo) toca o mesmo arquivo. Impossível testar isoladamente.
- **Recommendation:** Quebrar em `src/db/connection.js`, `src/controllers/{checkout,report,user}Controller.js`, `src/routes/index.js`, `src/services/{checkout,report}Service.js`. Compor em `app.js` (composition root).

### [HIGH] Callback Hell no /api/checkout com lógica de negócio (AP-010)
- **File:** `src/AppManager.js:28-78`
- **Description:** 4 níveis de callback aninhados (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`), com `if/else` de fluxo dentro de cada nível e tratamento de erro inconsistente. Cálculo de status de pagamento embutido (`status = cc.startsWith("4") ? "PAID" : "DENIED"`).
- **Impact:** Não é possível raciocinar sobre transação; erro em qualquer nível deixa estado parcial; cobertura de testes inviável.
- **Recommendation:** Migrar para `better-sqlite3` (síncrono, com `db.transaction()`) e mover o fluxo de checkout para `checkoutService.checkout({...})`. Controller fica com 3 linhas (parse → call service → respond).

### [HIGH] Checkout sem transação atômica (AP-012)
- **File:** `src/AppManager.js:50-63`
- **Description:** Sequência `INSERT enrollments` → `INSERT payments` → `INSERT audit_logs` sem `BEGIN/COMMIT`. Cada `db.run` é auto-commit.
- **Impact:** Falha entre o INSERT de payments e audit deixa cobrança registrada sem trilha de auditoria — ou pior, matrícula sem pagamento. Pesadelo de reconciliação.
- **Recommendation:** Envolver em `db.transaction(...)` (better-sqlite3) ou `BEGIN TRANSACTION; ... COMMIT;`. Rollback em qualquer falha.

### [HIGH] DELETE de usuário sem CASCADE deixa órfãos (AP-014)
- **File:** `src/AppManager.js:131-137`
- **Description:** `DELETE FROM users WHERE id = ?` sem deletar `enrollments`/`payments`/`audit_logs` correspondentes. A própria mensagem de resposta admite o problema: "matrículas e pagamentos ficaram sujos no banco".
- **Impact:** Integridade referencial quebrada; relatórios financeiros passam a contar dinheiro de usuários inexistentes.
- **Recommendation:** Adotar **soft delete** (`deleted_at` na coluna `users`) ou redefinir o schema com `ON DELETE CASCADE` nas FKs. Atualizar listagens para filtrar `WHERE deleted_at IS NULL`.

### [HIGH] Estado global mutável (AP-011)
- **File:** `src/utils.js:9-10`
- **Description:** `let globalCache = {}` e `let totalRevenue = 0` em escopo de módulo; `logAndCache` muta `globalCache` de qualquer chamada.
- **Impact:** Estado escondido entre módulos; race conditions impossíveis de reproduzir; testes não isolados.
- **Recommendation:** Encapsular em `src/services/cacheService.js` (`class CacheService { set/get/clear }`) exportando uma instância singleton intencional. `totalRevenue` deve sair daqui — ser derivado on-demand a partir do banco.

### [MEDIUM] N+1 query no /api/admin/financial-report (AP-015)
- **File:** `src/AppManager.js:80-129`
- **Description:** Itera `courses → enrollments → users → payments`, abrindo callback novo para cada nível. Para 10 cursos com 100 matrículas cada são ~2.000 queries por chamada.
- **Impact:** Endpoint inutilizável em produção; latência cresce em produto cartesiano.
- **Recommendation:** Substituir por uma única query agregada com `JOIN` e `GROUP BY`: `SELECT c.title, SUM(CASE WHEN p.status='PAID' THEN p.amount ELSE 0 END) AS revenue FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id LEFT JOIN payments p ON p.enrollment_id = e.id GROUP BY c.id`. Para "students", segunda query também consolidada.

### [MEDIUM] API deprecated: sqlite3 callback-style (AP-019)
- **File:** `src/AppManager.js:7, 10-22, 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 131`
- **Description:** Uso da API `node-sqlite3` com callbacks. O ecossistema migrou para `better-sqlite3` (síncrono, mais rápido, com transações nativas) ou `sqlite` (wrapper com promises) para projetos novos.
- **Impact:** Causa direta do callback hell; sem suporte ergonômico a transações; performance inferior.
- **Recommendation:** Migrar para `better-sqlite3@^11`. Cada `db.get`/`db.run`/`db.all` vira `db.prepare(sql).get/run/all`. `db.transaction(fn)` envolve o checkout. Atualizar `package.json`.

### [MEDIUM] Validação de payload ausente + nomes abreviados (AP-017, AP-025)
- **File:** `src/AppManager.js:29-35`
- **Description:** `req.body.usr, eml, pwd, c_id, card` lidos sem nenhum schema; só um `if (!u || !e || !cid || !cc)` superficial.
- **Impact:** Contrato da API incompreensível (`usr` é o quê? username? Sim — mas ninguém entenderia sem ler o código). Sem validação de formato de email ou de número de cartão.
- **Recommendation:** Adicionar `joi` ou `zod` como dependência. Definir `CheckoutSchema` com `{ name, email, password, courseId, card }` e validar no controller. Renomear campos no contrato (com período de compatibilidade se já houver clientes).

### [MEDIUM] Ausência de middleware de error handling (AP-018)
- **File:** `src/app.js:1-14` (ausência)
- **Description:** Não há `app.use((err, req, res, next) => …)`. Cada rota replica `res.status(500).send("Erro DB")` com strings genéricas.
- **Impact:** Mensagens de erro inconsistentes; erros internos não são logados estruturadamente; impossível mapear contagem de erros por endpoint.
- **Recommendation:** Criar `src/middlewares/errorHandler.js` que recebe `(err, req, res, next)`, loga via `pino` e responde JSON normalizado. Controllers passam a usar `next(err)`.

### [LOW] `let` para valores nunca reatribuídos (AP-022 variação)
- **File:** `src/AppManager.js:29-33, 46, 52, 81, 86, 90, 132`
- **Description:** Variáveis como `u`, `e`, `p`, `cid`, `cc`, `enrId`, `coursesPending`, `id` declaradas com `let` e nunca reatribuídas.
- **Impact:** Sinaliza descuido; em revisão, leitor precisa procurar reatribuições que não existem.
- **Recommendation:** Trocar por `const` onde aplicável. Reservar `let` apenas para contadores como `coursesPending`/`enrPending` que de fato são decrementados.

### [LOW] `console.log` como logger de produção (AP-021)
- **File:** `src/utils.js:13`; `src/AppManager.js:45`; `src/app.js:13`
- **Description:** Eventos importantes (cache write, boot do servidor, processamento de cartão) registrados com `console.log`.
- **Impact:** Sem nível, sem timestamp estruturado, sem correlação por request.
- **Recommendation:** Adicionar `pino` (ou `winston`). Em `src/utils/logger.js`, exportar logger estruturado. Substituir todos os `console.log`.

### [LOW] Magic numbers (port, "iterações" do badCrypto) (AP-022)
- **File:** `src/utils.js:6, 19`
- **Description:** `port: 3000` e `for (let i = 0; i < 10000; i++)` aparecem como literais sem nome.
- **Impact:** Intenção opaca; difícil de mudar com confiança.
- **Recommendation:** Porta para `process.env.PORT`. As "iterações" do `badCrypto` deixam de existir após TX-03.

================================
Total: 17 findings
================================

Phase 2 complete. Total: 17 findings (CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 3)
Proceed with refactoring (Phase 3)? [y/n]
> y
