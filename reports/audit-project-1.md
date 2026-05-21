================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, usuários, pedidos, itens_pedido)
Architecture:  Monolítica — 4 arquivos no root, sem separação de camadas; queries SQL, validação e roteamento misturados
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~615 lines of code
Date:    2026-05-20

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 4
Total: 18 findings

## Findings

### [CRITICAL] SQL Injection em massa (AP-002)
- **File:** `models.py:28, 47-50, 57-60, 68, 92, 109-111, 126-128, 140, 148-150, 155-160, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297`
- **Description:** Todas as queries do model são montadas por concatenação de string (`"SELECT * FROM produtos WHERE id = " + str(id)`, `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
- **Impact:** Qualquer parâmetro vindo do request (id, email, termo de busca, status) pode ser usado para extrair, modificar ou destruir o banco inteiro. Comprometimento total da camada de dados.
- **Recommendation:** Substituir por queries parametrizadas com placeholders posicionais: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`. Aplicar em todos os 24+ pontos identificados.

### [CRITICAL] Hardcoded SECRET_KEY (AP-001)
- **File:** `app.py:7`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` versionada diretamente no source.
- **Impact:** Compromete a assinatura de cookies/sessões do Flask. Atacante consegue forjar sessões em nome de qualquer usuário.
- **Recommendation:** Mover para `src/config/settings.py` lendo de `os.environ["SECRET_KEY"]` com falha explícita quando ausente. Criar `.env.example` com a chave documentada.

### [CRITICAL] Endpoint `/admin/query` executa SQL arbitrário (AP-003)
- **File:** `app.py:59-78`
- **Description:** Rota POST recebe `sql` no body JSON e executa diretamente via `cursor.execute(query)`, sem autenticação ou whitelist.
- **Impact:** Backdoor explícito de execução remota de SQL. Permite dump completo, alteração e drop de tabelas por qualquer cliente HTTP.
- **Recommendation:** Remover o endpoint. Se houver necessidade real de administração, expor um conjunto fechado de operações idempotentes via CLI ou rota autenticada com role-check.

### [CRITICAL] Senhas armazenadas e comparadas em plaintext (AP-004)
- **File:** `models.py:105-111, 122-131`; `database.py:75-83`
- **Description:** `login_usuario` compara `senha = '...'` diretamente no `WHERE` da query SQL; `criar_usuario` insere a senha sem hash; o seed insere `('admin', 'admin@loja.com', 'admin123', 'admin')`.
- **Impact:** Vazamento direto do banco entrega todas as senhas em texto. Comparação por SQL inviabiliza qualquer adoção de hash sem reescrita.
- **Recommendation:** Introduzir `src/services/auth_service.py` com `bcrypt` (`bcrypt.hashpw`/`bcrypt.checkpw`). Atualizar `criar_usuario`/`login_usuario` para usar `senha_hash`. Reseed com senhas hasheadas; em ambiente real, forçar reset.

### [CRITICAL] Secrets vazados em endpoint público `/health` (AP-005)
- **File:** `controllers.py:285-290`
- **Description:** Resposta de `GET /health` inclui `db_path`, `debug` e `secret_key: "minha-chave-super-secreta-123"`.
- **Impact:** Qualquer crawler ou monitor que consultar `/health` coleta a chave de assinatura de sessão. Compõe AP-001.
- **Recommendation:** Reduzir `/health` a `{"status": "ok", "database": "connected"}`. Não expor configuração interna em rota pública.

### [HIGH] `DEBUG=True` ligado em produção (AP-007)
- **File:** `app.py:8, 88`
- **Description:** `app.config["DEBUG"] = True` no carregamento e `app.run(debug=True)` no entry point.
- **Impact:** Em qualquer exception não tratada, o Flask serve um debugger interativo via web ao público, permitindo execução remota de código com o token PIN exposto nos logs.
- **Recommendation:** Ler `DEBUG` de env var (`os.environ.get("DEBUG", "false") == "true"`) no `src/config/settings.py`. Default `False`.

### [HIGH] God Module: `models.py` mistura DB, queries, formatação e regra (AP-008)
- **File:** `models.py:1-315`
- **Description:** Um único arquivo concentra acesso ao SQLite, montagem manual de DTOs, lógica de criação de pedido (validação de estoque + cálculo de total + atualização de estoque) e cálculo de relatório de vendas com faixas de desconto.
- **Impact:** Impossível testar uma regra (cálculo de desconto) sem subir conexão de banco. Mudanças em uma entidade afetam o arquivo inteiro.
- **Recommendation:** Separar em `src/models/{produto,usuario,pedido}.py` (acesso a dados) + `src/services/pedido_service.py` (regra de criação de pedido) + `src/services/relatorio_service.py` (faixas de desconto).

### [HIGH] Lógica de validação dentro dos Controllers (AP-009)
- **File:** `controllers.py:30-54, 72-90, 174, 200-201, 241-243`
- **Description:** Validações de domínio (preço >= 0, estoque >= 0, len(nome), categorias válidas, status válido) vivem dentro dos handlers `criar_produto`, `atualizar_produto`, `criar_pedido`, `atualizar_status_pedido`.
- **Impact:** Validação amarrada ao framework HTTP. Não reutilizável em jobs/CLI. Cada handler reimplementa a mesma checagem.
- **Recommendation:** Mover para schemas com `marshmallow` ou `pydantic` (`src/schemas/produto_schema.py`, etc.) e validar no controller em uma linha. Categorias e status válidos viram constantes em `src/models/` ou em `src/config/`.

### [HIGH] Notificações como side-effect dentro do controller (AP-013)
- **File:** `controllers.py:208-210, 248-250`
- **Description:** `print("ENVIANDO EMAIL: ...")`, `print("ENVIANDO SMS: ...")` dentro de `criar_pedido` e `atualizar_status_pedido` simulam notificações; não existe service.
- **Impact:** Lógica não-HTTP misturada com HTTP; impossível trocar para fila/worker; impossível testar sem capturar stdout.
- **Recommendation:** Extrair `src/services/notification_service.py` com métodos `notify_pedido_criado(pedido_id, usuario_id)`, `notify_status_changed(pedido_id, status)`. Controller só chama o serviço.

### [HIGH] Estado global mutável para conexão de banco (AP-011)
- **File:** `database.py:4-10`
- **Description:** Conexão SQLite é guardada em `global db_connection` com `check_same_thread=False`, reutilizada por todos os handlers.
- **Impact:** Sob carga concorrente do Flask, o mesmo cursor/conexão é compartilhado entre threads, gerando corrupção de leitura e perda de transações.
- **Recommendation:** Trocar por padrão "connection per request" usando `flask.g` (`g.db = sqlite3.connect(...)`) + `app.teardown_appcontext(close_db)`. Encapsular em `src/db/connection.py`.

### [HIGH] Transação ausente em `criar_pedido` (AP-012)
- **File:** `models.py:133-169`
- **Description:** Sequência de `INSERT pedidos` → `INSERT itens_pedido` → `UPDATE produtos.estoque` executada sem `BEGIN`/`COMMIT` único; cada `cursor.execute` é auto-commit.
- **Impact:** Falha no meio (ex.: item 3 de 5) deixa pedido criado mas com itens parciais e estoque parcialmente debitado. Banco inconsistente.
- **Recommendation:** Envolver em transação explícita (`with db: ...` no sqlite3 — context manager faz commit/rollback) dentro do `pedido_service.criar(...)`.

### [MEDIUM] Query N+1 em `get_pedidos_usuario` e `get_todos_pedidos` (AP-015)
- **File:** `models.py:172-200, 204-232`
- **Description:** Para cada pedido, abre cursor para itens; para cada item, abre cursor para buscar nome do produto. 1 + N + N×M queries por chamada.
- **Impact:** Latência cresce de forma quadrática com volume; em 100 pedidos com 5 itens cada, são 600 queries.
- **Recommendation:** Substituir por uma query consolidada com `JOIN`: `SELECT p.*, ip.*, pr.nome FROM pedidos p LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id LEFT JOIN produtos pr ON pr.id = ip.produto_id` e montar a hierarquia no Python.

### [MEDIUM] Senha incluída nos payloads de listagem (AP-005 mid-impact)
- **File:** `models.py:79-87, 95-103`
- **Description:** `get_todos_usuarios` e `get_usuario_por_id` montam dict com campo `senha` e retornam para os endpoints `/usuarios`.
- **Impact:** Mesmo que a senha estivesse hasheada, expor o hash em listagens pública facilita ataques offline. Hoje, com plaintext, é vazamento direto.
- **Recommendation:** Modelar uma serialização explícita sem o campo `senha`. Em ORM, usar `UserPublicSchema`. Aqui, basta omitir do dict.

### [MEDIUM] Paginação ausente em todas as listagens (AP-016)
- **File:** `controllers.py:5-12, 111-126, 128-134, 229-235`
- **Description:** `/produtos`, `/produtos/busca`, `/usuarios`, `/pedidos` retornam a tabela inteira sem `LIMIT`/`OFFSET`.
- **Impact:** Em produção, primeira leitura derruba o serviço.
- **Recommendation:** Aceitar `?page=1&page_size=50` (cap em 100) e aplicar `LIMIT ? OFFSET ?` nas queries.

### [MEDIUM] `try/except Exception` genérico em toda função (AP-018)
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`
- **Description:** Toda função de controller envelopa o corpo em `except Exception as e: return jsonify({"erro": str(e)}), 500`.
- **Impact:** Mensagem interna vaza para o cliente; bugs não chegam aos logs estruturados; nada de observabilidade.
- **Recommendation:** Centralizar em `src/middlewares/error_handler.py` registrando `@app.errorhandler(Exception)` que loga via `logging` e retorna `500 {"erro": "Internal Server Error"}`. Definir `HttpError` para erros esperados (400/404).

### [LOW] Categorias e status enumeráveis hardcoded como literal (AP-020)
- **File:** `controllers.py:52 ("categorias_validas"), 242 (status)`
- **Description:** `categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` e a lista de status válidos vivem dentro do controller.
- **Impact:** Duplicação latente — qualquer outro controller que precise validar reescreve a lista.
- **Recommendation:** Mover para constantes em `src/models/produto.py` (`CATEGORIAS`) e `src/models/pedido.py` (`STATUS_VALIDOS`). Importar onde necessário.

### [LOW] Logging com `print` em vez de `logging` (AP-021)
- **File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250`; `app.py:56, 83-86`
- **Description:** Eventos de domínio e erros são impressos com `print("...")`.
- **Impact:** Sem timestamps, sem níveis, sem correlação por request. Sem chances de ir para um agregador estruturado.
- **Recommendation:** Configurar `logging.getLogger(__name__)` em cada módulo. Substituir todos os `print` por `log.info`/`log.error`/`log.exception`.

### [LOW] Concatenação de string em vez de f-string (AP-023)
- **File:** `controllers.py:8, 11, 57, 106, 161, 179, 182, 208-210, 248-250`
- **Description:** `"Listando " + str(len(produtos)) + " produtos"` etc. em todo o controller.
- **Impact:** Legibilidade; estilo pré-Py3.6.
- **Recommendation:** Substituir por `f"Listando {len(produtos)} produtos"` (e, com o logger, por `log.info("Listando %d produtos", len(produtos))`).

### [LOW] Magic numbers em validações e regras de desconto (AP-022)
- **File:** `controllers.py:48-50, 113-114`; `models.py:257-262`
- **Description:** Limites de tamanho de nome (`< 2`, `> 200`), faixas de desconto (`> 10000`, `> 5000`, `> 1000`) e percentuais (`0.1`, `0.05`, `0.02`) aparecem como literais sem nome.
- **Impact:** Intenção opaca; difícil de mudar com confiança.
- **Recommendation:** Extrair para constantes nomeadas (`PRODUTO_NOME_MIN`, `DESCONTO_FAIXA_PREMIUM`, `DESCONTO_PERCENT_PREMIUM`) em `src/models/produto.py` e `src/services/relatorio_service.py`.

================================
Total: 18 findings
================================

Phase 2 complete. Total: 18 findings (CRITICAL: 5 | HIGH: 5 | MEDIUM: 4 | LOW: 4)
Proceed with refactoring (Phase 3)? [y/n]
> y
