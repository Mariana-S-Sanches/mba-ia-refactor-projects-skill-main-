# Template do Relatório de Auditoria (Fase 2)

O relatório deve ser impresso **idêntico** ao formato abaixo. Substitua os placeholders (`<...>`) pelos dados reais coletados nas Fases 1 e 2.

Salve o mesmo conteúdo em `reports/audit-project-<N>.md` (relativo à raiz do projeto auditado).

---

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto, igual ao nome da pasta raiz>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<L> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>
Total: <a+b+c+d> findings

## Findings

### [CRITICAL] <Nome curto do anti-pattern> (AP-XXX)
- **File:** `<arquivo>:<linha(s)>`
- **Description:** <descrição curta do código real encontrado>
- **Impact:** <consequência objetiva>
- **Recommendation:** <ação prescritiva — não genérica>

### [CRITICAL] <Próximo finding>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

================================
Total: <X> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> 
```

---

## Regras de escrita

1. **Ordem.** Sempre CRITICAL → HIGH → MEDIUM → LOW. Dentro de cada nível, ordene por arquivo.
2. **Linha exata.** Sempre `arquivo:linha` ou `arquivo:início-fim`. Sem aproximação. Sem "espalhado no arquivo".
3. **Descrição concreta.** Cite o código real, não definição teórica.
   - ✗ "Existe SQL Injection no projeto."
   - ✓ "`models.py:28` monta a query com `+ str(id)` concatenando input do request."
4. **Impacto objetivo.** Em uma linha, qual o risco prático.
5. **Recommendation prescritiva.** Diga **o que fazer**, não "considere melhorar".
   - ✗ "Considere usar prepared statements."
   - ✓ "Substituir por `cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))`."
6. **Cite o ID do anti-pattern do catálogo** (AP-XXX) — isso ajuda na rastreabilidade entre fases.
7. **Não invente findings.** Se não bater no catálogo nem tiver `arquivo:linha`, descarte.

---

## Exemplo curto (referência)

```markdown
### [CRITICAL] Hardcoded SECRET_KEY (AP-001)
- **File:** `app.py:7`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está versionado no source.
- **Impact:** Qualquer pessoa com acesso ao repositório consegue assinar tokens e abrir sessões em nome de outros usuários.
- **Recommendation:** Mover para variável de ambiente lida via `os.environ["SECRET_KEY"]` em `config/settings.py`, com fallback para erro explícito quando ausente. Adicionar `.env.example`.
```

---

## Fechamento obrigatório do relatório

A última linha do output do terminal **precisa** ser a pergunta de confirmação:

```
Phase 2 complete. Total: <N> findings (CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>)
Proceed with refactoring (Phase 3)? [y/n]
> 
```

A skill **não pode** prosseguir antes de receber `y`/`yes`/`sim`.
