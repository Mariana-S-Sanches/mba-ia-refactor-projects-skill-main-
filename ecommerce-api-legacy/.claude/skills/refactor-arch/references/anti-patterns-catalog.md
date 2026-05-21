# Catálogo de Anti-Patterns

Cada entrada traz: **sinal de detecção** (o que procurar concretamente), **severidade** (CRITICAL / HIGH / MEDIUM / LOW) e **observação curta sobre o impacto**.

Use este catálogo como checklist na Fase 2. Para cada arquivo de source code, percorra a lista inteira.

---

## CRITICAL — falhas graves de segurança ou arquitetura

### AP-001 — Hardcoded Credentials / Secrets
- **Sinal:** literais como `SECRET_KEY = "..."`, `password = "..."`, `api_key = "..."`, `paymentGatewayKey: "pk_live_..."` no source. Vale também para SMTP, DB user/pass, tokens.
- **Procure por (regex):** `(SECRET|PASS|KEY|TOKEN|PWD)\s*[:=]\s*["'][^"']{3,}["']`
- **Impacto:** vazamento ao primeiro `git clone`. Compromete autenticação, sessões e integrações externas.

### AP-002 — SQL Injection (queries por concatenação)
- **Sinal:** `cursor.execute("... " + var + " ...")`, `"SELECT * FROM ... WHERE id = " + str(id)`, template strings com interpolação direta de input.
- **Procure por:** `execute(`/`query(`/`db.run(` seguido de `+` ou `${` envolvendo `request.`/`req.body`/`req.params`.
- **Impacto:** RCE de banco. Comprometimento total dos dados.

### AP-003 — Endpoint que executa SQL ou código arbitrário
- **Sinal:** rotas como `/admin/query`, `/eval`, `/debug` que recebem `sql` ou código no body e executam via `cursor.execute(input)` ou `eval(input)`.
- **Impacto:** backdoor explícito.

### AP-004 — Senha sem hash seguro
- **Sinal:** comparação direta `senha == ...`, ou uso de `md5`/`sha1`/`base64`/`Buffer.from(...).toString('base64')` como "hash".
- **Procure por:** `hashlib.md5`, `hashlib.sha1`, `Buffer.from(pwd).toString('base64')`, comparação literal de senha em SQL.
- **Impacto:** senhas vazadas em segundos por dicionário ou rainbow tables. MD5/SHA1 para senhas é considerado quebrado.

### AP-005 — Exposição de secrets em response
- **Sinal:** endpoints (especialmente `/health`, `/status`, `/debug`) retornando `secret_key`, `debug`, `password` no JSON.
- **Impacto:** qualquer scraper coleta as credenciais.

### AP-006 — Dados sensíveis em logs
- **Sinal:** `console.log`/`print`/`logger.info` contendo `card`, `cvv`, `password`, `token`, `cpf`, `ssn`.
- **Impacto:** PCI/LGPD/GDPR violation; logs costumam ir para sistemas de terceiros.

### AP-007 — `DEBUG=True` / Modo desenvolvimento ligado em produção
- **Sinal:** `app.config['DEBUG'] = True`, `app.run(debug=True)`, `NODE_ENV` ausente, `Rails.env.development?` em produção.
- **Impacto:** console interativo / stack traces expostos publicamente.

---

## HIGH — fortes violações de MVC/SOLID

### AP-008 — God Class / God Module
- **Sinal:** arquivo único > 300 linhas que mistura configuração, definição de rotas, queries SQL, validação e formatação. Classes com >10 métodos públicos de responsabilidades distintas.
- **Heurística rápida:** se o arquivo tem `import sqlite3` **e** `from flask import` **e** `def criar_*(...)` que retorna JSON — é God Module.
- **Impacto:** impossível testar isoladamente; qualquer mudança afeta tudo.

### AP-009 — Lógica de negócio dentro de Controllers/Routes
- **Sinal:** validações de domínio, regras de desconto, cálculo de preço, decisões de status dentro de funções de rota (`@app.route`, `app.post`, `def get_tasks()`).
- **Procure por:** `if priority < 1 or priority > 5`, `if categoria not in [...]`, `if status == 'aprovado'` dentro de handler HTTP.
- **Impacto:** acoplamento forte com HTTP; impossível reutilizar a regra fora do request; testes exigem subir framework.

### AP-010 — Callback Hell / Promise Pyramid
- **Sinal:** ≥ 3 níveis aninhados de callback assíncrono em `db.get(... (err, x) => db.get(... (err, y) => ...))`. Vale também para `.then().then().then()` profundo.
- **Impacto:** tratamento de erro inconsistente; impossível raciocinar sobre transações.

### AP-011 — Estado global mutável
- **Sinal:** `let cache = {}`, `globalCache`, `global db_connection` em escopo de módulo, modificado de fora.
- **Impacto:** estado escondido; race conditions; testes não isolados.

### AP-012 — Transação ausente em operação composta
- **Sinal:** múltiplos `INSERT`/`UPDATE`/`DELETE` sequenciais sem `BEGIN/COMMIT/ROLLBACK` ou `db.session.commit()` único ao final. Especialmente em checkouts, transferências, criação de pedido com itens.
- **Impacto:** falha parcial deixa banco inconsistente (cobrança feita sem matrícula registrada).

### AP-013 — Service layer ausente ou morto
- **Sinal:** notificações/integrações externas (email, SMS, push) feitas inline em controllers via `print("ENVIANDO EMAIL")`, **ou** uma `class NotificationService` declarada mas nunca instanciada/importada.
- **Impacto:** lógica não-HTTP misturada com HTTP; ou pior, ilusão de modularidade.

### AP-014 — Foreign key violation por delete sem CASCADE
- **Sinal:** `DELETE FROM users WHERE id = ?` sem antes deletar registros dependentes em `enrollments`, `payments`, `tasks` etc., e schema sem `ON DELETE CASCADE`.
- **Impacto:** registros órfãos, integridade referencial quebrada.

---

## MEDIUM — padronização, performance moderada

### AP-015 — Query N+1
- **Sinal:** `for x in lista: cursor.execute("SELECT ... WHERE fk = " + x.id)`. Vale também para `User.query.get(t.user_id)` dentro de loop em ORMs.
- **Procure por:** loop (`for`, `forEach`, `map`) contendo qualquer chamada ao banco.
- **Impacto:** explosão de queries; latência cresce linear com N.

### AP-016 — Paginação ausente
- **Sinal:** `GET /<recurso>` sem parâmetros `page`/`limit`/`offset` e sem `.limit(...)` na query.
- **Impacto:** dump completo da tabela em cada chamada; degrada conforme a base cresce.

### AP-017 — Validação de payload ausente ou duplicada
- **Sinal:** ausência de schema (`pydantic`, `marshmallow`, `joi`, `zod`, `express-validator`) **OU** mesma validação repetida em vários handlers.
- **Impacto:** inconsistência de contrato; mudanças exigem caçar todos os pontos.

### AP-018 — `try/except` ou `try/catch` genérico que engole erros
- **Sinal:** `except Exception as e: return jsonify({"erro": str(e)}), 500`, `try { ... } catch(e) {}`, `bare except:` (Python).
- **Impacto:** bugs invisíveis; observabilidade zero; muitas vezes vaza mensagem interna para o cliente.

### AP-019 — API deprecated em uso
- **Sinal específico por stack:**
  - Python: `urllib2`, `imp`, `optparse`, `print` sem parêntese (Py2), `flask.json` removido em 2.3+, `flask-script`.
  - Node: `request`, `crypto.createCipher` (use `createCipheriv`), `Buffer()` constructor, sqlite3 callback-style (preferir `better-sqlite3` ou `sqlite` com promises).
  - Ruby: `Fixnum`/`Bignum` (use `Integer`), `URI.escape`.
  - Java: `Date` mutável (use `java.time`).
- **Impacto:** quebra em upgrade de runtime; falta de manutenção; vulnerabilidades não corrigidas.

### AP-020 — Categorias / status / regras enumeráveis hardcoded como lista solta
- **Sinal:** `if categoria not in ["informatica", "moveis", ...]` espalhado em vários arquivos.
- **Impacto:** duplicação; mudança exige alterar múltiplos pontos.

---

## LOW — legibilidade / qualidade

### AP-021 — Logging com `print`/`console.log`
- **Sinal:** chamadas de `print`/`console.log` no source de produção.
- **Impacto:** sem níveis, sem timestamp estruturado, sem correlação.

### AP-022 — Magic numbers
- **Sinal:** literais numéricos (`5000`, `100`, `0.05`, `10000`) usados sem nome em validações ou cálculos.
- **Impacto:** intenção opaca; difícil de mudar.

### AP-023 — Concatenação de string em vez de formatação
- **Sinal:** `"texto " + str(x) + " mais"` em vez de `f"texto {x} mais"` (Python) ou template literals (JS).
- **Impacto:** legibilidade; performance marginal.

### AP-024 — Imports não utilizados
- **Sinal:** `import json, os, sys, time` em arquivo que não usa nenhum desses.
- **Impacto:** ruído; sinal de copy-paste.

### AP-025 — Nomes ruins / abreviações sem contexto
- **Sinal:** `usr`, `eml`, `pwd`, `c_id`, `cc` em payloads de API; variáveis de 1 letra fora de loops.
- **Impacto:** API incompreensível para clientes.

### AP-026 — `type(x) == list` em Python
- **Sinal:** comparação direta de tipo em vez de `isinstance(x, list)`.
- **Impacto:** falha em subclasses; quebra de Liskov.

### AP-027 — Aninhamento profundo de `if/else`
- **Sinal:** ≥ 3 níveis de `if/else` para retornar boolean.
- **Impacto:** legibilidade; convide ao bug.

### AP-028 — Comentários ausentes em código não-óbvio / falta de docstrings
- **Sinal:** funções públicas sem docstring/JSDoc; lógica não-trivial sem comentário.
- **Impacto:** onboarding lento; documentação implícita.

---

## Como usar esse catálogo na Fase 2

1. Faça **uma passagem por arquivo**: para cada arquivo source, vá descendo o catálogo do CRITICAL para o LOW.
2. Anote o `arquivo:linha` exato — se o anti-pattern aparece em várias linhas, liste o intervalo (`models.py:28, 47-50, 68`).
3. Pode acontecer de um mesmo sintoma se encaixar em **mais de um** anti-pattern (ex.: senha em plaintext é AP-004 e também AP-005 se for exposta) — registre como findings separados.
4. Garanta a cobertura dos mínimos do enunciado:
   - ≥ 5 findings totais
   - ≥ 1 CRITICAL ou HIGH
   - Inclui detecção de API deprecated (AP-019) se aplicável.
