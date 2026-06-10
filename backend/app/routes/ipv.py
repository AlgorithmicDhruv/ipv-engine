import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.utils.db import get_db_session
from app.models.models import IPVResult, TraderValuation
from app.services.reconciliation import ReconciliationService

logger = logging.getLogger(__name__)
ipv_bp = Blueprint("ipv", __name__, url_prefix="/api/v1/ipv")


@ipv_bp.route("/results", methods=["GET"])
def get_results():
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        limit = min(int(request.args.get("limit", 100)), 500)
        offset = int(request.args.get("offset", 0))

        results = (
            session.query(IPVResult)
            .order_by(IPVResult.reconciled_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return jsonify([r.to_dict() for r in results]), 200
    except SQLAlchemyError as e:
        logger.error("DB error fetching IPV results: %s", str(e))
        return jsonify({"error": "Database error."}), 500


@ipv_bp.route("/breaches", methods=["GET"])
def get_breaches():
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        breaches = (
            session.query(IPVResult)
            .filter(IPVResult.breach_flag == 1)
            .order_by(IPVResult.reconciled_at.desc())
            .all()
        )
        return jsonify({
            "total_breaches": len(breaches),
            "breaches": [r.to_dict() for r in breaches]
        }), 200
    except SQLAlchemyError as e:
        logger.error("DB error fetching breaches: %s", str(e))
        return jsonify({"error": "Database error."}), 500


@ipv_bp.route("/reconcile/pending", methods=["POST"])
def reconcile_pending():
    session_gen = get_db_session()
    session = next(session_gen)
    try:
        svc = ReconciliationService(session)
        results = svc.reconcile_all_pending()
        next(session_gen, None)
        return jsonify({
            "processed": len(results),
            "results": results
        }), 200
    except SQLAlchemyError as e:
        logger.error("DB error during batch reconciliation: %s", str(e))
        return jsonify({"error": "Database error."}), 500
