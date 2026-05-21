"""Notificações de domínio — implementação simples baseada em logger.

Em produção, trocar por adapters reais (SES, Twilio, FCM) sem alterar a
interface usada pelo Pedido Service.
"""
from __future__ import annotations

from src.utils.logger import get_logger

log = get_logger(__name__)


def notify_pedido_criado(pedido_id: int, usuario_id: int) -> None:
    log.info("pedido.criado pedido_id=%s usuario_id=%s", pedido_id, usuario_id)
    log.info("notification.email pedido_id=%s", pedido_id)
    log.info("notification.sms pedido_id=%s", pedido_id)
    log.info("notification.push pedido_id=%s", pedido_id)


def notify_status_changed(pedido_id: int, novo_status: str) -> None:
    log.info("pedido.status_changed pedido_id=%s status=%s", pedido_id, novo_status)
    if novo_status == "aprovado":
        log.info("notification.preparar_envio pedido_id=%s", pedido_id)
    elif novo_status == "cancelado":
        log.info("notification.devolver_estoque pedido_id=%s", pedido_id)
