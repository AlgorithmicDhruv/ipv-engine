import os
import logging
from flask import Flask, jsonify
from app.routes.valuations import valuations_bp
from app.routes.ipv import ipv_bp
from app.routes.instruments import instruments_bp, prices_bp

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(valuations_bp)
    app.register_blueprint(ipv_bp)
    app.register_blueprint(instruments_bp)
    app.register_blueprint(prices_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
