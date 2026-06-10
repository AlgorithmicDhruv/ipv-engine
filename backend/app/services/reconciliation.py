import os
import logging
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from app.models.models import TraderValuation, MarketPrice, IPVResult, Instrument

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD_PCT = Decimal(os.environ.get("BREACH_THRESHOLD_PCT", "0.5"))


class ReconciliationService:
    """
    Computes variance between trader-submitted valuations and independent
    market prices. Flags breaches where variance exceeds the configured threshold.
    """

    def __init__(self, session: Session, threshold_pct: Decimal = DEFAULT_THRESHOLD_PCT):
        self.session = session
        self.threshold_pct = threshold_pct

    def reconcile_valuation(self, valuation_id: int) -> IPVResult:
        valuation = self.session.get(TraderValuation, valuation_id)
        if valuation is None:
            raise ValueError(f"Valuation {valuation_id} not found.")

        market_price = (
            self.session.query(MarketPrice)
            .filter(
                MarketPrice.instrument_id == valuation.instrument_id,
                MarketPrice.price_date == valuation.valuation_date,
                MarketPrice.is_stale == 0
            )
            .order_by(MarketPrice.ingested_at.desc())
            .first()
        )

        if market_price is None:
            raise ValueError(
                f"No independent market price found for instrument "
                f"{valuation.instrument_id} on {valuation.valuation_date}."
            )

        trader_price = Decimal(str(valuation.submitted_price))
        independent_price = Decimal(str(market_price.market_price))

        variance_abs = abs(trader_price - independent_price)
        variance_pct = (variance_abs / independent_price) * Decimal("100")
        breach = variance_pct > self.threshold_pct

        result = IPVResult(
            valuation_id=valuation.valuation_id,
            market_price_id=market_price.price_id,
            trader_price=trader_price,
            independent_price=independent_price,
            variance_abs=variance_abs,
            variance_pct=variance_pct,
            breach_flag=1 if breach else 0,
            threshold_pct=self.threshold_pct
        )

        valuation.status = "BREACHED" if breach else "VERIFIED"

        self.session.add(result)
        self.session.flush()

        logger.info(
            "Reconciled valuation %d: trader=%.6f independent=%.6f "
            "variance_pct=%.4f%% breach=%s",
            valuation_id, trader_price, independent_price, variance_pct, breach
        )

        return result

    def reconcile_all_pending(self) -> list[dict]:
        pending = (
            self.session.query(TraderValuation)
            .filter(TraderValuation.status == "PENDING")
            .all()
        )

        results = []
        for val in pending:
            try:
                result = self.reconcile_valuation(val.valuation_id)
                results.append({
                    "valuation_id": val.valuation_id,
                    "status": "reconciled",
                    "breach": bool(result.breach_flag)
                })
            except ValueError as e:
                logger.warning("Skipped valuation %d: %s", val.valuation_id, str(e))
                results.append({
                    "valuation_id": val.valuation_id,
                    "status": "skipped",
                    "reason": str(e)
                })

        return results
