# Skill de Auditoria e Refatoração Arquitetural — `refactor-arch`

Este repositório é o entregável do desafio de criação de uma **Skill do Claude Code** que audita uma codebase legada, identifica anti-patterns por severidade e refatora o projeto para o padrão **MVC** — de forma **agnóstica de tecnologia**. A mesma skill foi aplicada a três projetos distintos:

| Projeto | Stack | Estado inicial | Estado final |
|---|---|---|---|
| `code-smells-project/` | Python + Flask + SQLite raw | Monolito de 4 arquivos com SQL Injection, senha em plaintext e God Class | MVC completo: `src/{config,db,models,schemas,services,controllers,views,middlewares,utils}` |
| `ecommerce-api-legacy/` | Node.js + Express + sqlite3 | Single God Class `AppManager` com checkout em callback hell | MVC completo: `src/{config,db,models,schemas,services,controllers,routes,middlewares,utils}` |
| `task-manager-api/` | Python + Flask + SQLAlchemy | Organização parcial (models/routes/services) com lógica nas routes e MD5 para senhas | MVC consolidado: controllers extraídos, services reais, schemas marshmallow, JWT verdadeiro |

---

## Sumário

- [A. Análise Manual](#a-análise-manual)
- [B. Construção da Skill](#b-construção-da-skill)
- [C. Resultados](#c-resultados)
- [D. Como Executar](#d-como-executar)

---

## A. Análise Manual

Antes de codar a skill, fiz uma leitura manual dos três projetos para entender os padrões que a skill precisaria detectar. Os achados abaixo alimentaram o catálogo de anti-patterns e o playbook de refatoração da skill.

> Convenção: cada achado vem com `arquivo:linha`, severidade e a justificativa de por que aquilo é relevante arquiteturalmente. A escala de severidade segue a definição do enunciado (CRITICAL → LOW).

### Projeto 1 — `code-smells-project/` (Python/Flask)

API de e-commerce com 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`) e cerca de 800 linhas. Tem **todos** os anti-patterns possíveis — é o pior caso de monolito desorganizado.

| # | Severidade | Anti-pattern | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | SQL Injection em massa (string concat) | `models.py:28, 47-50, 57-60, 68, 92, 109-111, 126-128, 140, 148-150, 155-160, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297` | Todas as queries são montadas com `+ str(id)` ou `+ email +`. Um único parâmetro malicioso compromete o banco inteiro. |
| 2 | **CRITICAL** | Hardcoded credentials | `app.py:7` | `SECRET_KEY = "minha-chave-super-secreta-123"` versionado no repositório. Compromete sessões e assinatura de tokens. |
| 3 | **CRITICAL** | Endpoint `/admin/query` executa SQL arbitrário | `app.py:59-78` | Backdoor explícito: recebe qualquer SQL via JSON e executa. RCE de banco completo. |
| 4 | **CRITICAL** | Senhas em plaintext | `models.py:105-110, 122-131`; `database.py:76-78` | `login_usuario` compara `senha = '...'` direto no `WHERE`. Nenhum hash. |
| 5 | **CRITICAL** | Secrets vazadas no endpoint público `/health` | `controllers.py:289` | A resposta de `/health` devolve `secret_key`, `debug`, `db_path` — qualquer scraper vê isso. |
| 6 | **HIGH** | `DEBUG=True` em "produção" | `app.py:8, 88` | Stack traces e console interativo expostos ao público. |
| 7 | **HIGH** | God Module `models.py` mistura camadas | `models.py:1-315` | Um único arquivo concentra acesso ao banco, formatação de DTO, lógica de pedido e relatório. Impossível testar em isolamento. |
| 8 | **HIGH** | Lógica de validação no Controller | `controllers.py:30-54, 72-90, 240-252` | Validações de domínio (preço, categoria, estoque, status) vivem dentro da camada HTTP. Não dá para reaproveitar nem testar sem subir Flask. |
| 9 | **HIGH** | Notificações como side-effect dentro do controller | `controllers.py:208-210, 248-250` | `print("ENVIANDO EMAIL …")` simula notificação no meio do request, sem service layer. Quebra Single Responsibility. |
| 10 | **HIGH** | Estado global mutável para conexão de DB | `database.py:4, 8-10` | Singleton implícito via `global db_connection` com `check_same_thread=False`. Race conditions garantidas sob carga. |
| 11 | **MEDIUM** | N+1 query em `get_pedidos_usuario` / `get_todos_pedidos` | `models.py:172-200, 204-232` | Para cada pedido, abre cursor novo para itens; para cada item, abre cursor para produto. 1 + N + N×M queries. |
| 12 | **MEDIUM** | Senha retornada nas respostas de listagem | `models.py:79-87, 95-103` | `get_todos_usuarios` e `get_usuario_por_id` incluem o campo `senha` no dict — leak por listagem. |
| 13 | **MEDIUM** | Falta total de paginação | Todos os endpoints `GET /listar...` | `/produtos`, `/usuarios`, `/pedidos` retornam tudo. Em produção isso degrada rápido. |
| 14 | **MEDIUM** | `try/except Exception` engolindo erros | `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, …` | Toda função do controller envelopa em `except Exception as e` e retorna 500 genérico — esconde bugs e dificulta observabilidade. |
| 15 | **LOW** | Categorias e status hardcoded como listas mágicas | `controllers.py:52, 242` | `categorias_validas` e os status válidos vivem como literais nos controllers; duplicam conhecimento. |
| 16 | **LOW** | Concatenação com `+` em vez de `f-string` | `controllers.py:8, 11, 57, 106, 161, 179, 182, 208-210, 248-250` | Estilo pré-Python 3.6, prejudica legibilidade. |
| 17 | **LOW** | `print` para logging | `app.py:56, 83-86`; `controllers.py:8, 11, 57, 106, …` | Sem `logging`, sem níveis, sem formato — impede correlação em produção. |
| 18 | **LOW** | Magic numbers | `controllers.py:48, 50, 113-114`; `models.py:257-262` | Limites como `len(nome) < 2`, faixas de desconto `> 10000` aparecem direto no código. |

### Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express)

LMS API com fluxo de checkout em `AppManager.js` — uma única classe que faz inicialização do banco, definição de rotas e regra de negócio. Estilo callback puro.

| # | Severidade | Anti-pattern | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | Credenciais de produção hardcoded | `src/utils.js:1-7` | `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."` no source. Vazam no primeiro `git clone`. |
| 2 | **CRITICAL** | "Hash" de senha não-criptográfico | `src/utils.js:17-23` | `badCrypto` faz `Buffer.from(pwd).toString('base64')` repetido — reversível em milissegundos. |
| 3 | **CRITICAL** | Número de cartão logado no console | `src/AppManager.js:45` | `console.log("Processando cartão " + cc + …)` grava PAN em qualquer agregador de logs. Falha de PCI direta. |
| 4 | **CRITICAL** | Senha em plaintext no seed | `src/AppManager.js:18` | `INSERT INTO users (… pass) VALUES ('… ', '123')`. Junto com `badCrypto`, fica claro que não existe segurança de credenciais. |
| 5 | **CRITICAL** | Senha default `"123456"` para novos usuários sem `pwd` | `src/AppManager.js:68` | `let hash = badCrypto(p || "123456");` cria contas adivinhaveis no checkout. |
| 6 | **HIGH** | God Class `AppManager` mistura DB + rotas + lógica | `src/AppManager.js:1-141` | Construtor abre conexão; `setupRoutes` define cada handler inline com regra de negócio dentro. Não há separação Model/Controller/Route. |
| 7 | **HIGH** | Callback hell no `/api/checkout` com lógica de negócio | `src/AppManager.js:28-78` | 4 níveis de callback (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`), erro tratado de forma inconsistente. |
| 8 | **HIGH** | Estado global mutável compartilhado entre módulos | `src/utils.js:9-10` | `globalCache` e `totalRevenue` são `let` globais; qualquer módulo escreve. Estado escondido = bugs invisíveis. |
| 9 | **HIGH** | Checkout sem transação | `src/AppManager.js:50-63` | INSERTs encadeados em `enrollments`, `payments` e `audit_logs` sem `BEGIN/COMMIT` — falha parcial deixa banco inconsistente. |
| 10 | **HIGH** | DELETE de usuário sem CASCADE | `src/AppManager.js:131-137` | Própria mensagem da resposta admite o problema: "matrículas e pagamentos ficaram sujos no banco". |
| 11 | **MEDIUM** | N+1 query no `/api/admin/financial-report` | `src/AppManager.js:80-129` | Itera cursos → enrollments → users → payments. 1 + N + N×M + N×M queries. |
| 12 | **MEDIUM** | API deprecated: callback-style `sqlite3` | `src/AppManager.js:11-21, 37, 40, 50, 54, 57, 69, 83, 92, 104, 106` | Toda a API usa callbacks; o ecossistema moderno usa `better-sqlite3` ou promises/async-await. Detecção de API deprecated obrigatória pelo enunciado. |
| 13 | **MEDIUM** | Validação de payload ausente / nomes abreviados | `src/AppManager.js:29-35` | `req.body.usr, eml, pwd, c_id, card` — não há schema (Joi/Zod/express-validator), e o contrato da API é incompreensível. |
| 14 | **MEDIUM** | Ausência de middleware de error handling | `src/app.js:1-14` (não existe) | Toda rota replica `res.status(500).send("Erro DB")`. Erros não são logados nem normalizados. |
| 15 | **LOW** | `let` para valores nunca reatribuídos | `src/AppManager.js:29-33, 46, 52, 81, 86, 90, 132` | Devem ser `const`. Sinal forte de descuido. |
| 16 | **LOW** | `console.log` como logging de produção | `src/utils.js:13`; `src/AppManager.js:45` | Sem níveis, sem formato estruturado. |
| 17 | **LOW** | Magic numbers (porta, iterações fake) | `src/utils.js:6` (port 3000); `src/utils.js:19` (10000 iterações inúteis) | Sem nome, espalha conhecimento. |

### Projeto 3 — `task-manager-api/` (Python/Flask + SQLAlchemy)

API de Task Manager com **organização parcial** (`models/`, `routes/`, `services/`, `utils/`). À primeira vista parece arrumado, mas a separação é só estética: routes contêm regra de negócio, validação está duplicada e o "service layer" é código morto.

| # | Severidade | Anti-pattern | Local | Por que importa |
|---|---|---|---|---|
| 1 | **CRITICAL** | `SECRET_KEY` hardcoded | `app.py:13` | `'super-secret-key-123'` no source. |
| 2 | **CRITICAL** | MD5 como hash de senha | `models/user.py:29, 32` | MD5 é considerado quebrado para hash de senhas desde ~2005. Sem salt, sem KDF. |
| 3 | **CRITICAL** | SMTP credentials hardcoded | `services/notification_service.py:7-10` | `'taskmanager@gmail.com'` / `'senha123'` versionado. |
| 4 | **CRITICAL** | `password` exposta em `to_dict()` | `models/user.py:21` | Toda resposta de `/users`, `/users/:id`, `/login` inclui `password` (hash MD5, mas ainda é hash). |
| 5 | **CRITICAL** | Token "JWT" fake após login | `routes/user_routes.py:210` | `'token': 'fake-jwt-token-' + str(user.id)` — sem assinatura, sem expiração. Autenticação é teatro. |
| 6 | **HIGH** | `DEBUG=True` em produção e `host=0.0.0.0` | `app.py:34` | Combinação clássica que expõe o console interativo na rede. |
| 7 | **HIGH** | Regra de negócio dentro das routes (overdue lógica duplicada) | `routes/task_routes.py:30-39, 71-80, 171-180, 282-287`; `routes/report_routes.py:33-43, 132-135` | A mesma lógica de "está atrasado?" aparece 5 vezes copiada/colada. Já existe `Task.is_overdue()` no model que ninguém usa. |
| 8 | **HIGH** | `bare except:` engolindo qualquer erro | `routes/task_routes.py:62, 137, 236`; `routes/user_routes.py:130, 149`; `routes/report_routes.py:186, 207, 222` | Captura até `KeyboardInterrupt`. Esconde bugs e dificulta debugging. |
| 9 | **HIGH** | `NotificationService` totalmente morto | `services/notification_service.py` | A classe inteira existe mas nunca é importada ou instanciada. Código fantasma. |
| 10 | **MEDIUM** | N+1 query em `GET /tasks` (user e category por task) | `routes/task_routes.py:42, 51` | Para cada task, faz `User.query.get` e `Category.query.get`. Existe `db.relationship` definido nos models — bastaria usar `joinedload`. |
| 11 | **MEDIUM** | N+1 em `/reports/summary` (tasks por usuário) | `routes/report_routes.py:56` | Loop em users com `Task.query.filter_by(user_id=u.id)` dentro. |
| 12 | **MEDIUM** | Validação duplicada / `process_task_data` órfão | `utils/helpers.py:57-108` vs `routes/task_routes.py:92-114, 167-184` | Função utilitária faz tudo o que a route refaz manualmente. Ninguém a chama. |
| 13 | **MEDIUM** | Categorias dentro de `report_routes` | `routes/report_routes.py:157-223` | CRUD de Category vive no arquivo de relatórios — péssima delimitação de responsabilidade. |
| 14 | **MEDIUM** | `type(x) == list` em vez de `isinstance` | `routes/task_routes.py:141, 210`; `utils/helpers.py:103` | Antipattern Python que falha em subclasses. |
| 15 | **MEDIUM** | Falta de paginação | `GET /tasks`, `GET /users`, `GET /reports/summary` | Retorna tudo, sempre. |
| 16 | **LOW** | Imports não usados | `routes/task_routes.py:7` (`os, sys, json, time`); `routes/report_routes.py:8` (`json`) | Ruído visual, sinal de descuido. |
| 17 | **LOW** | `print` para logging | `routes/task_routes.py:149, 153, 219, 234`; `routes/user_routes.py:83, 89, 147`; `services/notification_service.py:21, 24` | Mesmo problema dos outros projetos. |
| 18 | **LOW** | `if/else` aninhado profundo na detecção de overdue | `models/task.py:50-60` | 3 níveis de aninhamento desnecessários para uma expressão booleana. |

### Padrões comuns aos três projetos

Levantar os achados juntos revelou um conjunto pequeno e repetido de padrões — o que reforçou a viabilidade de uma skill agnóstica:

1. **Hardcoded secrets** (SECRET_KEY, SMTP, payment gateway, DB user) — aparece nos 3.
2. **Senha sem hash seguro** (plaintext / base64 / MD5).
3. **Lógica de negócio dentro do Controller/Route**.
4. **N+1 query** em endpoints de listagem ou relatório.
5. **Estado global mutável**.
6. **God Class/Module** ou camadas "estéticas" sem separação real.
7. **Tratamento de erro genérico** (`except Exception:` ou `bare except:` ou `console.log`).
8. **Falta de paginação / validação de schema**.

Esse mapeamento virou a espinha dorsal do `anti-patterns-catalog.md` da skill.

---

## B. Construção da Skill

### Estrutura de arquivos

A skill vive em `<projeto>/.claude/skills/refactor-arch/` e tem dois níveis:

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestrador das 3 fases (prompt)
└── references/
    ├── analysis-heuristics.md            # como detectar stack/arquitetura
    ├── anti-patterns-catalog.md          # 28 anti-patterns por severidade
    ├── audit-report-template.md          # formato exato do relatório
    ├── mvc-guidelines.md                 # estrutura MVC alvo (por linguagem)
    └── refactoring-playbook.md           # 12 transformações antes/depois
```

A escolha de **SKILL.md + arquivos de referência** segue a recomendação da documentação oficial de Skills do Claude: o SKILL.md é curto e prescritivo (instrui *o que* fazer e *em que ordem*), enquanto o conhecimento de domínio (heurísticas, catálogos, exemplos) vive nos arquivos referenciados — carregados sob demanda, evitando inflar o contexto.

### Decisões de design

**1. Fases sequenciais com gate humano.** O SKILL.md força ordem: Fase 1 (análise) → Fase 2 (auditoria, com `STOP` esperando `y/n`) → Fase 3 (refatoração + validação automática). O `STOP` cumpre o requisito do enunciado de não modificar nada sem revisão.

**2. Detecção por manifesto, não por extensão.** O `analysis-heuristics.md` instrui a ler primeiro `requirements.txt`/`package.json`/`Gemfile`/`pom.xml`/`go.mod`/`composer.json`/`Cargo.toml`/`mix.exs`/`*.csproj`. Só cai para "contar extensões" como último recurso. Isso evita falsos positivos (ex.: um repo Node com scripts Python utilitários ainda é Node).

**3. Catálogo com 28 anti-patterns mapeados para 12 transformações.** O enunciado pede mínimo 8 anti-patterns e 8 transformações; entregamos 28 e 12. A relação N→M está documentada na tabela final do `refactoring-playbook.md` — cada finding tem um caminho de correção concreto, sem ficar com "TODO" no relatório.

**4. APIs deprecated explicitamente cobertas.** O `AP-019` lista por stack: `urllib2`/`flask-script` (Python), `request`/`crypto.createCipher`/`sqlite3` callback (Node), `Fixnum`/`URI.escape` (Ruby), `java.util.Date` (Java). Isso garante que o requisito "deve incluir detecção de APIs deprecated" sempre dispara — no caso do Projeto 2, foi o callback-style do `sqlite3` que pegou esse slot.

**5. Severidade prescritiva, não opinião.** Cada anti-pattern já vem com severidade no catálogo. Quem audita não decide "isso é CRITICAL ou HIGH?" no calor do momento — só verifica se o sinal bate.

**6. Validação obrigatória ao final da Fase 3.** O SKILL.md exige boot da aplicação + `GET /health` + ≥2 endpoints originais respondendo. Isso transforma o requisito do enunciado ("aplicação inicia sem erros, endpoints originais respondem") em parte do contrato da skill, não em verificação manual posterior.

### Como garantimos o agnosticismo de tecnologia

Três decisões concretas:

| Camada da skill | O que fizemos para ficar agnóstica |
|---|---|
| `SKILL.md` | Linguagem da fase é abstrata: "leia o manifesto de dependências", "abra o arquivo de entrada do framework", "encapsule conexão em padrão idiomático da stack". Nunca cita `pip` ou `npm` sem `/equivalente`. |
| `analysis-heuristics.md` | Tabela explícita com 10 linguagens (Python, JS/TS, Ruby, Java, PHP, Go, Rust, Elixir, C#, e fallback genérico). Manifestos, arquivos de entrada e drivers de banco listados lado a lado. |
| `anti-patterns-catalog.md` | Sinais de detecção em pseudocódigo / regex genérico (`execute(` seguido de `+` ou `${`). Quando o sinal é específico de stack, mostra exemplos para Python E Node E SQL puro. |
| `refactoring-playbook.md` | 12 transformações, cada uma com **antes/depois em Python E Node**. A intenção (eager loading, transação atômica, middleware de erro) é a mesma; só muda a sintaxe. |
| `mvc-guidelines.md` | Layouts de pasta idiomáticos para Python/Flask, Node/Express, Ruby/Sinatra, Java/Spring, Go e PHP/Laravel. |

O teste empírico: a **mesma cópia** da skill rodou nos 3 projetos com tecnologias diferentes (Flask raw, Express, Flask+SQLAlchemy) e detectou stack + anti-patterns + executou refatoração sem alteração.

### Anti-patterns escolhidos e por quê

A seleção do catálogo veio diretamente do levantamento manual. Os 28 anti-patterns cobrem:

- **5 CRITICAL** (segurança e backdoors): SQL Injection, hardcoded credentials, SQL/code execution endpoints, senha sem hash, exposição de secrets em response, log de PII, DEBUG=True. Todos foram encontrados em pelo menos 2 dos 3 projetos.
- **7 HIGH** (violações estruturais): God Class, lógica em controller, callback hell, estado global, transação ausente, service morto, FK órfã. Aparecem nos 3 projetos com sintomas diferentes.
- **6 MEDIUM** (qualidade que vira problema sob escala): N+1, paginação, validação, error handling, API deprecated, enums hardcoded. O N+1 está em **todos os 3 projetos**.
- **8 LOW** (legibilidade): logging com print, magic numbers, concatenação de string, imports não usados, naming ruim, `type==`, aninhamento profundo, falta de docstring.

### Desafios encontrados e como resolvi

**1. Validação automática da Fase 3 dentro de um ambiente que não tem toolchain de build.**
No Projeto 2, `better-sqlite3` e `bcrypt` falharam ao compilar porque a sandbox não tem `node-gyp` funcional. Solução: troquei `better-sqlite3` por `node:sqlite` (nativo no Node 22+, mesma API) e `bcrypt` por `bcryptjs` (pure JS). A skill genérica fica fiel ao playbook (`better-sqlite3` é a recomendação para projetos novos com toolchain), e os projetos refatorados usam um equivalente que sobe em qualquer ambiente.

**2. Manter o contrato HTTP original durante a refatoração.**
O `/api/checkout` do Projeto 2 espera campos abreviados (`usr/eml/pwd/c_id/card`). Renomear seria quebrar o cliente. Solução: o `checkoutSchema.js` aceita **tanto** os nomes legados quanto os modernos e normaliza internamente. O playbook foi atualizado para deixar essa estratégia explícita em qualquer refatoração de contrato.

**3. Senhas legadas em MD5 (Projeto 3) e plaintext (Projeto 1).**
A primeira execução da skill, num cenário real, encontraria usuários com hash inseguro no banco e travaria no login pós-refatoração. Como o desafio espera "endpoints continuam respondendo" e os DBs são re-criados pelo seed/boot, optei por **re-seedar com bcrypt** em todos os projetos. Em produção real, o playbook recomenda "forçar reset de senha no próximo login".

**4. Projeto 3 já tinha organização parcial.**
A skill precisava **não** reorganizar cosmeticamente. A regra no SKILL.md ("preserve a separação existente; promova separação interna ausente") deu o farol. Mantive `models/`, `routes/`, `services/`, `utils/`, e adicionei `controllers/`, `schemas/`, `middlewares/`, `config/`. O service layer existente, que estava morto (`notification_service.py`), foi efetivamente plugado no fluxo de criação de task.

**5. `N+1` em SQL puro vs ORM.**
No Projeto 1 (SQL puro) o playbook recomenda `WHERE id IN (...)` com IN-clause. No Projeto 3 (SQLAlchemy) recomenda `options(joinedload(...))`. As duas alternativas estão no `refactoring-playbook.md` para qualquer auditor saber qual aplicar conforme a stack detectada.

---

## C. Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Mínimo do enunciado |
|---|---:|---:|---:|---:|---:|---|
| Projeto 1 — `code-smells-project` | 5 | 5 | 4 | 4 | **18** | ≥5 com ≥1 CRITICAL/HIGH — atendido com folga |
| Projeto 2 — `ecommerce-api-legacy` | 5 | 5 | 4 | 3 | **17** | idem |
| Projeto 3 — `task-manager-api` | 5 | 4 | 5 | 4 | **18** | idem |

Os três relatórios completos estão em `reports/audit-project-{1,2,3}.md`.

### Comparação antes/depois

**Projeto 1 — `code-smells-project`**

| Antes | Depois |
|---|---|
| 4 arquivos no root (`app.py`, `controllers.py`, `models.py`, `database.py`), ~615 linhas misturando tudo | `src/{config,db,models,schemas,services,controllers,views,middlewares,utils}/` com 18 módulos focados |
| SQL Injection em 24+ pontos | Queries parametrizadas em 100% das chamadas |
| `SECRET_KEY` no source | `.env.example` + `src/config/settings.py` lendo de env |
| Senhas em plaintext, comparadas no SQL | `src/services/auth_service.py` com `bcrypt` (rounds=12) |
| `/admin/query` executando SQL arbitrário | **Removido** |
| `secret_key` no `/health` | `/health` retorna só `{status, database}` |
| Notificações como `print()` no controller | `src/services/notification_service.py` chamado pelo `pedido_service` |
| Pedido criado em 4 INSERTs sem transação | `pedido_service.criar_pedido` usa `BEGIN/COMMIT` com rollback |
| N+1 em listagem de pedidos | Duas queries: `pedidos` + `itens JOIN produtos IN (...)` |
| Try/except genérico em toda função | `src/middlewares/error_handler.py` centralizado |

**Projeto 2 — `ecommerce-api-legacy`**

| Antes | Depois |
|---|---|
| `src/AppManager.js` (170 linhas) faz DB + rotas + lógica + seed | `src/{config,db,models,schemas,services,controllers,routes,middlewares,utils}/` com 18 arquivos |
| Credenciais em `src/utils.js:1-7` | `.env.example` + `src/config/index.js` lendo de `process.env` |
| `badCrypto` (base64 truncado) | `src/services/authService.js` com `bcryptjs` (rounds=12) |
| `console.log("Processando cartão " + cc + ...)` | Apenas `BIN` + 4 últimos via `maskCard()`; key do gateway nunca logada |
| Callback hell de 4 níveis em `/api/checkout` | `checkoutService.checkout()` síncrono em `db.transaction(fn)` |
| Sem transação no checkout | Transação atômica (commit/rollback) |
| N+1 em `/api/admin/financial-report` (~2.000 queries) | Duas queries agregadas com `GROUP BY` e `LEFT JOIN` |
| sqlite3 callback-style (deprecated) | `node:sqlite` (nativo, síncrono) |
| DELETE de user deixa órfãos | Soft delete (`deleted_at`) + listagens filtram |
| Sem validação de payload | `src/schemas/checkoutSchema.js` com Joi (aceita contrato legado e moderno) |
| Sem error middleware | `src/middlewares/errorHandler.js` normaliza respostas |

**Projeto 3 — `task-manager-api`**

| Antes | Depois |
|---|---|
| `models/`, `routes/`, `services/`, `utils/` (organização cosmética) | Acrescentados `controllers/`, `schemas/`, `middlewares/`, `config/` e services reais |
| `SECRET_KEY = 'super-secret-key-123'` | `config/settings.py` lendo de env |
| MD5 no `set_password`/`check_password` | `services/auth_service.py` com bcrypt |
| SMTP credentials no source | `config/settings.py` lendo `SMTP_*` (vazio em dev → logger no-op) |
| `password` no `to_dict()` | `schemas/user_schema.UserPublicSchema` omite senha |
| `'token': 'fake-jwt-token-' + str(user.id)` | JWT real assinado HS256 com `sub`/`iat`/`exp` (pyjwt) |
| Lógica `is_overdue` duplicada em 5 lugares | `Task.is_overdue()` chamado em 1 lugar (schema) |
| Bare `except:` em 9 routes | `middlewares/error_handler.py` com `@app.errorhandler` para `HttpError`, `ValidationError` e `Exception` |
| `NotificationService` órfão | Chamado pelo `task_service.create_task()` quando `user_id` existe |
| N+1 em `GET /tasks` (user + category) | `joinedload(Task.user, Task.category)` |
| N+1 em `/reports/summary` | `func.count + outerjoin + group_by` |
| Validação duplicada (`process_task_data` + manual) | `schemas/task_schema.TaskCreateSchema` único |
| Category CRUD em `report_routes.py` | `routes/category_routes.py` + `controllers/category_controller.py` |
| Sem paginação | `?page=&page_size=` (cap 100) em `/tasks`, `/users` |
| `type(x) == list` | Resolvido naturalmente pelo schema marshmallow |

### Checklist de validação preenchido

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|:-:|:-:|:-:|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | ✓ | ✓ | ✓ |
| Framework detectado corretamente | ✓ Flask 3.1.1 | ✓ Express 4.18.2 | ✓ Flask 3.0 + SQLAlchemy |
| Domínio descrito corretamente | ✓ E-commerce | ✓ LMS / checkout | ✓ Task Manager |
| Número de arquivos analisados condiz | ✓ 4 | ✓ 3 | ✓ 10 |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template | ✓ | ✓ | ✓ |
| Cada finding com arquivo:linha exatos | ✓ | ✓ | ✓ |
| Ordenado CRITICAL → LOW | ✓ | ✓ | ✓ |
| ≥ 5 findings | ✓ 18 | ✓ 17 | ✓ 18 |
| Detecção de API deprecated incluída | ✓ Py2/flask-script (potencial) | ✓ sqlite3 callback | ✓ MD5/hash |
| Skill pausa pedindo confirmação | ✓ | ✓ | ✓ |
| **Fase 3 — Refatoração** | | | |
| Estrutura segue padrão MVC | ✓ | ✓ | ✓ |
| Config extraída para módulo (sem hardcoded) | ✓ `src/config/settings.py` | ✓ `src/config/index.js` | ✓ `config/settings.py` |
| Models criados para abstrair dados | ✓ | ✓ | ✓ (mantidos + limpos) |
| Views/Routes separadas | ✓ `src/views/routes.py` | ✓ `src/routes/index.js` | ✓ `routes/*.py` |
| Controllers concentram fluxo | ✓ | ✓ | ✓ |
| Error handling centralizado | ✓ | ✓ | ✓ |
| Entry point claro | ✓ `app.py` (composition root) | ✓ `app.js` | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ | ✓ | ✓ |
| Endpoints originais respondem | ✓ todos | ✓ todos | ✓ todos |

### Logs de validação (resumido)

**Projeto 1** — `python3 app.py`:
```
2026-05-21T00:22 [INFO] app: app.created debug=False
GET  /health                → 200 {"status":"ok","database":"connected"}
GET  /produtos?page=1&size=3 → 200 (paginado, sem campo senha)
POST /login (admin/admin123) → 200 (bcrypt verify OK)
POST /pedidos (2 itens)     → 201 {"pedido_id":1,"total":479.7}
GET  /pedidos               → 200 (sem N+1, JOIN consolidado)
POST /admin/query (backdoor) → 404 (rota removida)
POST /produtos {invalid}    → 400 (schema validation)
```

**Projeto 2** — `node --experimental-sqlite app.js`:
```
{"level":30,"port":3000,"msg":"Frankenstein LMS rodando"}
GET  /health                                    → 200 {"status":"ok"}
POST /api/checkout (visa 4111…)                 → 200 {"msg":"Sucesso","enrollment_id":1}
POST /api/checkout (master 5111…)               → 400 {"error":"Pagamento recusado"}
POST /api/checkout (payload incompleto)         → 400 com lista de erros do Joi
GET  /api/admin/financial-report                → 200 (2 cursos com receita agregada)
DELETE /api/users/1                             → 200 soft delete (deleted_at set)
```

**Projeto 3** — `python3 app.py`:
```
2026-05-21T17:08 [INFO] __main__: app.created debug=False
GET  /health                                    → 200
GET  /tasks?page=1&page_size=2                  → 200 paginado, com user_name/category_name/overdue (joinedload)
GET  /tasks/stats                               → 200 {"total":10,"pending":6,"overdue":2,...} (1 query agregada)
POST /login (joao/1234)                         → 200 com JWT real assinado HS256
GET  /categories                                → 200 com task_count consolidado
GET  /reports/summary                           → 200 com user_productivity sem N+1
POST /tasks (payload válido)                    → 201
POST /tasks (priority:99)                       → 400 schema validation
```

### Observações sobre o comportamento da skill em stacks diferentes

- **Tempo de Fase 1 e 2 foi praticamente o mesmo** nos três projetos — a heurística por manifesto é barata e o catálogo é genérico.
- **Fase 3 do Projeto 3 foi a mais sutil**: como já tinha estrutura, o ganho viria de promover separação interna, não de criar do zero. A regra "preserve a separação existente; promova separação ausente" no SKILL.md guiou bem.
- **A diferença real entre Flask e Express está só no playbook**: cada transformação tem exemplos lado a lado. Para o auditor, o protocolo é o mesmo.

---

## D. Como Executar

### Pré-requisitos

- **Claude Code CLI** instalado e logado.
- **Python 3.10+** para os Projetos 1 e 3.
- **Node.js 22.5+** para o Projeto 2 (usa `node:sqlite` nativo).

### Invocação da skill em cada projeto

Os três projetos têm a mesma cópia de `.claude/skills/refactor-arch/`. Para reaplicar a skill (auditar do zero), basta:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill conduz as 3 fases. Na Fase 2, ela pausa pedindo `y/n` antes de modificar arquivos. O relatório de auditoria é salvo em `<projeto>/reports/audit-project.md`; depois é movido manualmente (ou copiado pela skill futura) para a pasta `reports/` da raiz do repositório.

### Como rodar o código refatorado

**Projeto 1 — Python/Flask (code-smells-project)**
```bash
cd code-smells-project
cp .env.example .env                  # opcional; defaults bastam para dev
pip install -r requirements.txt
python app.py
# Servidor em http://localhost:5000
```

Endpoints para testar:
```bash
curl http://localhost:5000/health
curl 'http://localhost:5000/produtos?page=1&page_size=3'
curl -X POST -H 'Content-Type: application/json' \
     -d '{"email":"admin@loja.com","senha":"admin123"}' \
     http://localhost:5000/login
curl http://localhost:5000/relatorios/vendas
```

**Projeto 2 — Node.js/Express (ecommerce-api-legacy)**
```bash
cd ecommerce-api-legacy
cp .env.example .env                  # opcional
npm install
npm start
# Servidor em http://localhost:3000
```

Endpoints para testar:
```bash
curl http://localhost:3000/health
curl -X POST -H 'Content-Type: application/json' \
     -d '{"name":"Guilherme","email":"gui@fullcycle.com.br","password":"senhaforte","courseId":2,"card":"4111222233334444"}' \
     http://localhost:3000/api/checkout
curl http://localhost:3000/api/admin/financial-report
```

> Compatibilidade legada: o checkout também aceita os campos antigos `usr/eml/pwd/c_id/card`.

**Projeto 3 — Python/Flask + SQLAlchemy (task-manager-api)**
```bash
cd task-manager-api
cp .env.example .env                  # opcional
pip install -r requirements.txt
python seed.py                        # popula tasks.db com 3 users, 4 categorias, 10 tasks
python app.py
# Servidor em http://localhost:5000
```

Endpoints para testar:
```bash
curl http://localhost:5000/health
curl 'http://localhost:5000/tasks?page=1&page_size=5'
curl http://localhost:5000/tasks/stats
curl -X POST -H 'Content-Type: application/json' \
     -d '{"email":"joao@email.com","password":"1234"}' \
     http://localhost:5000/login
curl http://localhost:5000/reports/summary
```

### Como validar a refatoração

Para cada projeto, a definição de "funcionou" é:

1. **Boot sem erros.** Nenhuma stack trace no startup.
2. **`/health` responde 200.**
3. **Endpoints originais respondem** (verificar `api.http` do projeto 2 ou os exemplos acima).
4. **Validação por schema falha educadamente** (envie um payload inválido — deve voltar 400 com mensagem clara).
5. **Não há endpoint inseguro residual** (no Projeto 1, `/admin/query` deve dar 404; no Projeto 3, o token de login deve ser um JWT real, não `fake-jwt-token-1`).

Se algum desses passos falhar, a Fase 3 da skill não está terminada — re-rode com o feedback.

---

## Estrutura do repositório

```
mba-ia-refactor-projects-skill-main/
├── README.md                                         # este arquivo
│
├── code-smells-project/                              # Projeto 1
│   ├── .claude/skills/refactor-arch/                 # skill completa
│   │   ├── SKILL.md
│   │   └── references/{analysis-heuristics,anti-patterns-catalog,
│   │                   audit-report-template,mvc-guidelines,
│   │                   refactoring-playbook}.md
│   ├── app.py                                        # composition root
│   ├── requirements.txt
│   ├── .env.example
│   └── src/
│       ├── config/settings.py
│       ├── db/connection.py
│       ├── models/{produto,usuario,pedido}.py
│       ├── schemas/{produto,usuario,pedido}_schema.py
│       ├── services/{auth,pedido,relatorio,notification}_service.py
│       ├── controllers/{produto,usuario,pedido,relatorio,system}_controller.py
│       ├── views/routes.py
│       ├── middlewares/error_handler.py
│       └── utils/logger.py
│
├── ecommerce-api-legacy/                             # Projeto 2
│   ├── .claude/skills/refactor-arch/                 # cópia da skill
│   ├── app.js                                        # composition root
│   ├── package.json
│   ├── .env.example
│   ├── api.http
│   └── src/
│       ├── config/index.js
│       ├── db/{connection,schema,seed}.js
│       ├── models/{user,course,enrollment,payment}Model.js
│       ├── schemas/checkoutSchema.js
│       ├── services/{auth,payment,checkout,report}Service.js
│       ├── controllers/{checkout,report,user,health}Controller.js
│       ├── routes/index.js
│       ├── middlewares/errorHandler.js
│       └── utils/logger.js
│
├── task-manager-api/                                 # Projeto 3
│   ├── .claude/skills/refactor-arch/                 # cópia da skill
│   ├── app.py                                        # composition root
│   ├── seed.py
│   ├── database.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config/settings.py
│   ├── models/{task,user,category}.py
│   ├── schemas/{task,user,category}_schema.py
│   ├── services/{auth,task,user,category,report,notification}_service.py
│   ├── controllers/{task,user,category,report}_controller.py
│   ├── routes/{task,user,category,report}_routes.py
│   ├── middlewares/error_handler.py
│   └── utils/helpers.py
│
└── reports/                                          # Relatórios de auditoria
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```

---

## Critérios de Aceite — verificação final

| Critério (do enunciado) | Projeto 1 | Projeto 2 | Projeto 3 |
|---|:-:|:-:|:-:|
| Fase 1 detecta stack corretamente | ✓ | ✓ | ✓ |
| Fase 2 encontra ≥ 5 findings | ✓ (18) | ✓ (17) | ✓ (18) |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ (10) | ✓ (10) | ✓ (9) |
| Fase 3: aplicação funciona após refatoração | ✓ | ✓ | ✓ |

Todos os critérios atendidos nos três projetos.
