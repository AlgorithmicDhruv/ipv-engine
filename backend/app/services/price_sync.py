import logging
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.models import Instrument, MarketPrice
from app.utils.redis_client import get_all_price_keys, consume_prices

logger = logging.getLogger(__name__)


class PriceSyncService:
    """
    Reads market price records from the Redis feed and persists them
    into the PostgreSQL market_prices table. This mirrors the pattern
    of transferring data from a NoSQL event store into a relational
    database for structured querying and auditability.
    """

    def __init__(self, session: Session):
        self.session = session

    def sync_all(self) -> dict:
        keys = get_all_price_keys()
        total_written = 0
        total_skipped = 0
        errors = []

        for key in keys:
            ticker = key.split(":", 1)[-1]
            instrument = (
                self.session.query(Instrument)
                .filter(Instrument.ticker == ticker, Instrument.is_active == 1)
                .first()
            )

            if instrument is None:
                logger.warning("No active instrument found for ticker %s — skipping.", ticker)
                total_skipped += 1
                continue

            records = consume_prices(ticker)
            for record in records:
                try:
                    price_date = datetime.strptime(record["price_date"], "%Y-%m-%d").date()
                    existing = (
                        self.session.query(MarketPrice)
                        .filter(
                            MarketPrice.instrument_id == instrument.instrument_id,
                            MarketPrice.price_source == record["source"],
                            MarketPrice.price_date == price_date
                        )
                        .first()
                    )
                    if existing:
                        total_skipped += 1
                        continue

                    mp = MarketPrice(
                        instrument_id=instrument.instrument_id,
                        price_source=record["source"],
                        market_price=record["price"],
                        price_date=price_date
                    )
                    self.session.add(mp)
                    total_written += 1

                except (KeyError, ValueError) as e:
                    logger.error("Malformed price record for %s: %s", ticker, str(e))
                    errors.append({"ticker": ticker, "error": str(e)})

        self.session.flush()
        logger.info("Price sync complete — written: %d, skipped: %d", total_written, total_skipped)

        return {
            "written": total_written,
            "skipped": total_skipped,
            "errors": errors
        }
