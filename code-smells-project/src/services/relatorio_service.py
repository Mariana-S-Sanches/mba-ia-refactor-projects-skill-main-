"""Cálculo do relatório de vendas — faixas de desconto como constantes."""
from __future__ import annotations

from src.models import pedido as pedido_model


# Faixas de desconto aplicáveis ao faturamento bruto.
# Cada tupla é (limite_minimo_inclusivo, percentual).
DESCONTO_FAIXAS: tuple[tuple[float, float], ...] = (
    (10_000.0, 0.10),
    (5_000.0, 0.05),
    (1_000.0, 0.02),
)


def _calcular_desconto(faturamento: float) -> float:
    for limite, percentual in DESCONTO_FAIXAS:
        if faturamento > limite:
            return faturamento * percentual
    return 0.0


def relatorio_vendas() -> dict:
    agg = pedido_model.aggregate_report()
    faturamento = float(agg["faturamento"] or 0)
    desconto = _calcular_desconto(faturamento)
    total_pedidos = agg["total"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": agg["pendentes"],
        "pedidos_aprovados": agg["aprovados"],
        "pedidos_cancelados": agg["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
