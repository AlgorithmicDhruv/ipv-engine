import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.utils.db import get_db_session
from app.models.models import TraderValuation, Instrument
from app.services.reconciliation import ReconciliationService

logger = logging.getLogger(__name__)
valuations_bp = Blueprint("valuations", __name__, url_prefix="/api/v1/valuations")


@valuations_bp.route("", methods=["POST"])
def submit_valuation():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    required = ["ticker", "trader_id", "submitted_price", "position_quantity", "valuation_date"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    session_gen = get_db_session()
    session = next(session_gen)
    try:
        instrument = (
            session.query(Instrument)
            .filter(Instrument.ticker == data["ticker"], Instrument.is_active == 1)
            .first()
        )
        if instrument is None:
            return jsonify({"error": f"Instrument '{data['ticker']}' not found or inactive."}), 404

        try:
            val_date = datetime.strptime(data["valuation_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "valuation_date must be in YYYY-MM-DD format."}), 400

        valuation = TraderValuation(
            instrument_id=instrument.instrument_id,
            trader_id=data["trader_id"],
            submitted_price=data["submitted_price"],
            position_quantity=data["position_quantity"],
            valuation_date=val_date,
            source_system=data.get("source_system", "QUARTZ")
        )
        session.add(valuation)
        session.flush()

        # Attempt immediate reconciliation if market price is available
        try:
            svc = ReconciliationService(session)
            result = svc.reconcile_valuation(valuation.valuation_id)
            response_data = {
                "valuation": valuation.to_dict(),
                "ipv_result": result.to_dict()
            }
        except ValueError:
            response_data = {
                "valuation": valuation.to_dict(),
                "ipv_result": None,
                "message": "No market price available yet. Valuation queued for reconciliation."
            }

        next(session_gen, None)
        return jsonify(response_data), 201

    except SQLAlchemyError as e:
        logger.error("DB error on valuation submit: %s", str(e))
        return jsonify({"error": "Database error."}), 500


@valuations_bp.route("/<int:instrument_id>", methods=["GET"])
def get_valuations(instrument_id: int):
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        valuations = (
            session.query(TraderValuation)
            .filter(TraderValuation.instrument_id == instrument_id)
            .order_by(TraderValuation.valuation_date.desc())
            .all()
        )
        return jsonify([v.to_dict() for v in valuations]), 200
    except SQLAlchemyError as e:
        logger.error("DB error fetching valuations: %s", str(e))
        return jsonify({"error": "Database error."}), 500
