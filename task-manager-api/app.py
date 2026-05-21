"""Composition root da Task Manager API."""
from __future__ import annotations

import datetime
import logging
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import settings
from database import db
from middlewares import error_handler
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def _setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def create_app() -> Flask:
    _setup_logging()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.SECRET_KEY

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)

    @app.route("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.datetime.utcnow())}

    @app.route("/")
    def index():
        return {"message": "Task Manager API", "version": "2.0"}

    error_handler.register(app)

    with app.app_context():
        db.create_all()

    logging.getLogger(__name__).info("app.created debug=%s", settings.DEBUG)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
