# Heurísticas de Análise de Projeto

Como detectar **linguagem, framework, banco e arquitetura** sem assumir uma stack específica.

---

## 1. Detecção de linguagem e framework

A regra geral é: **manifesto > arquivo de entrada > extensão dos arquivos > convenção**.

### 1.1 Por manifesto de dependências

| Arquivo | Linguagem | Como extrair informação |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | Procure `flask`, `django`, `fastapi`, `starlette`, `bottle`, `sanic`, `tornado`, `aiohttp`. A versão fica na própria linha (`flask==3.1.1`). |
| `package.json` | JavaScript/TypeScript | Em `dependencies` procure `express`, `koa`, `fastify`, `hapi`, `nestjs`, `next`, `nuxt`. A versão fica no valor. |
| `Gemfile`, `Gemfile.lock` | Ruby | Procure `rails`, `sinatra`, `hanami`, `roda`. |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java/Kotlin | Procure `spring-boot-starter-web`, `javalin`, `micronaut`, `ktor`. |
| `composer.json` | PHP | Procure `laravel/framework`, `symfony/symfony`, `slim/slim`. |
| `go.mod` | Go | Procure `gin-gonic/gin`, `gofiber/fiber`, `labstack/echo`, `gorilla/mux`. |
| `Cargo.toml` | Rust | Procure `axum`, `actix-web`, `rocket`, `warp`. |
| `mix.exs` | Elixir | Procure `phoenix`, `plug_cowboy`. |
| `Project.toml` ou `*.csproj` | C# | Procure `Microsoft.AspNetCore.*`. |

### 1.2 Por arquivo de entrada

Quando o manifesto não for conclusivo, abra os arquivos mais prováveis:

- Python: `app.py`, `main.py`, `wsgi.py`, `asgi.py`, `manage.py`, `server.py`
- Node.js: `app.js`, `index.js`, `server.js`, `src/app.js`, `src/index.js`, `src/server.js`, `src/main.ts`
- Ruby: `config.ru`, `app.rb`, `application.rb`
- Java: `*Application.java`, `Main.java`
- PHP: `index.php`, `public/index.php`
- Go: `main.go`, `cmd/*/main.go`

E inspecione os imports/usings das primeiras linhas.

### 1.3 Por extensão (último recurso)

Se nada acima funcionar, conte extensões dominantes (`*.py`, `*.js`, `*.ts`, `*.rb`, `*.go`, `*.java`, `*.php`, `*.rs`, `*.ex`, `*.cs`).

---

## 2. Detecção de banco de dados

Cheque, em ordem:

1. **Strings de conexão** em arquivos de configuração ou source: `postgres://`, `mysql://`, `sqlite:///`, `mongodb://`, `redis://`.
2. **Imports/dependências**:
   - Python: `sqlite3`, `psycopg2`, `mysqlclient`, `pymongo`, `sqlalchemy`, `tortoise-orm`, `peewee`, `mongoengine`.
   - Node: `sqlite3`, `better-sqlite3`, `pg`, `mysql2`, `mongodb`, `mongoose`, `sequelize`, `typeorm`, `prisma`, `knex`.
   - Ruby: ActiveRecord adapters (`pg`, `mysql2`, `sqlite3`).
   - Java: JDBC drivers, JPA.
3. **Comandos `CREATE TABLE` ou migrations** dentro do código revelam as entidades.
4. **Pastas `migrations/`, `db/`, `prisma/`, `schema.sql`, `seed.*`** indicam o schema.

Liste as tabelas/entidades reais, não as inferidas — se houver `CREATE TABLE produtos`, escreva `produtos`.

---

## 3. Inferência do domínio

Combine essas pistas em uma frase curta:

- Nomes das rotas (`/produtos`, `/checkout`, `/tasks`).
- Nomes das tabelas/entidades (`pedidos`, `enrollments`, `tasks/users/categories`).
- Comentários e `README.md` do projeto, quando disponível.
- Nome do projeto na raiz (`package.json` "name", primeiro `<h1>` do README).

Exemplos esperados:
- "E-commerce API (produtos, pedidos, usuários)"
- "LMS API com fluxo de checkout (cursos, matrículas, pagamentos)"
- "Task Manager (tasks, usuários, categorias, relatórios)"

---

## 4. Classificação da arquitetura atual

Compare a estrutura de pastas/arquivos contra as opções abaixo:

| Sinal observado | Classificação |
|---|---|
| Tudo em 1–4 arquivos no root, sem pastas | **Monolítica — script único** |
| Uma única classe/módulo "Manager/Helper/Core" concentra tudo | **God Class / Monolito orientado a objeto** |
| Pastas `models/`, `views/`, `controllers/` (ou `routes/`) | **MVC tradicional** |
| `models/`, `routes/`, `services/`, `utils/` (sem controllers) | **MVC parcial — Active Record-ish** |
| `domain/`, `application/`, `infrastructure/` | **Hexagonal / Ports & Adapters** |
| `entities/`, `usecases/`, `repositories/` | **Clean Architecture** |
| Pacotes por feature (`users/`, `orders/`) com sub-camadas dentro | **Modular monolith / Feature folders** |
| Múltiplos serviços com seus próprios manifestos | **Microservices** |

Sempre adicione uma observação livre, ex.: "Monolítica — tudo em 4 arquivos, sem separação de camadas".

---

## 5. Contagem de arquivos e linhas

- "Source files analyzed" = arquivos de código-fonte (excluindo `node_modules/`, `.venv/`, `dist/`, lockfiles, assets, migrations geradas).
- "~N lines of code" = soma das linhas dos arquivos source. Use estimativa por contagem direta (`wc -l`) ignorando linhas em branco quando possível.

---

## 6. Bandeiras vermelhas a procurar já na Fase 1

Anote (mas só relate na Fase 2) se identificar de cara:
- Falta de `requirements.txt`/`package.json` / lockfile desatualizado.
- Múltiplas versões major do mesmo framework no histórico de dependências.
- Pasta `tests/` vazia ou ausente.
- Arquivo `.env` committado.
- Versão de runtime declarada no `package.json` ou `setup.py` muito antiga (Node < 18, Python < 3.10, Ruby < 3).
