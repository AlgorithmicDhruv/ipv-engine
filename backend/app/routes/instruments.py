import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.utils.db import get_db_session
from app.models.models import Instrument, MarketPrice
from app.services.price_sync import PriceSyncService
from app.utils.redis_client import publish_price

logger = logging.getLogger(__name__)
instruments_bp = Blueprint("instruments", __name__, url_prefix="/api/v1/instruments")
prices_bp = Blueprint("prices", __name__, url_prefix="/api/v1/prices")


@instruments_bp.route("", methods=["GET"])
def list_instruments():
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        instruments = (
            session.query(Instrument)
            .filter(Instrument.is_active == 1)
            .order_by(Instrument.asset_class, Instrument.ticker)
            .all()
        )
        return jsonify([i.to_dict() for i in instruments]), 200
    except SQLAlchemyError as e:
        logger.error("DB error listing instruments: %s", str(e))
        return jsonify({"error": "Database error."}), 500


@prices_bp.route("/sync", methods=["POST"])
def sync_prices():
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        svc = PriceSyncService(session)
        summary = svc.sync_all()
        next(session_gen, None)
        return jsonify(summary), 200
    except SQLAlchemyError as e:
        logger.error("DB error during price sync: %s", str(e))
        return jsonify({"error": "Database error."}), 500


@prices_bp.route("/publish", methods=["POST"])
def publish_price_to_feed():
    """
    Test/simulation endpoint for pushing a market price into the Redis feed.
    In production this would be replaced by a market data vendor connector.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    required = ["ticker", "price", "source", "price_date"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        publish_price(
            ticker=data["ticker"],
            price=float(data["price"]),
            source=data["source"],
            price_date=data["price_date"]
        )
        return jsonify({"status": "published", "ticker": data["ticker"]}), 200
    except Exception as e:
        logger.error("Failed to publish price to Redis: %s", str(e))
        return jsonify({"error": str(e)}), 500
