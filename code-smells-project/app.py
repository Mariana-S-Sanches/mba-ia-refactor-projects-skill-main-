"""Composition root da API — cria o Flask, compõe peças e sobe."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.db.connection import init_db
from src.middlewares import error_handler
from src.utils.logger import get_logger, setup_logging
from src.views.routes import register as register_routes


def create_app() -> Flask:
    setup_logging()
    log = get_logger(__name__)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app)
    init_db(app)
    register_routes(app)
    error_handler.register(app)

    log.info("app.created debug=%s", settings.DEBUG)
    return app


app = create_app()


if __name__ == "__main__":
    get_logger(__name__).info(
        "server.start host=%s port=%s debug=%s", settings.HOST, settings.PORT, settings.DEBUG
    )
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
