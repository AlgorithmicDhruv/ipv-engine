from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    SmallInteger, ForeignKey, Sequence
)
from sqlalchemy.orm import relationship
from app.utils.db import Base


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = {"schema": "ipv"}
    # __table_args__ = {}

    instrument_id = Column(
        Integer,
        Sequence("instruments_seq", schema="ipv"),
        primary_key=True
    )
    ticker = Column(String(20), nullable=False, unique=True)
    description = Column(String(200), nullable=False)
    asset_class = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    is_active = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    valuations = relationship("TraderValuation", back_populates="instrument")
    market_prices = relationship("MarketPrice", back_populates="instrument")

    def to_dict(self) -> dict:
        return {
            "instrument_id": self.instrument_id,
            "ticker": self.ticker,
            "description": self.description,
            "asset_class": self.asset_class,
            "currency": self.currency,
            "is_active": bool(self.is_active)
        }


class TraderValuation(Base):
    __tablename__ = "trader_valuations"
    __table_args__ = {"schema": "ipv"}
    # __table_args__ = {}

    valuation_id = Column(
        Integer,
        Sequence("valuations_seq", schema="ipv"),
        primary_key=True
    )
    instrument_id = Column(Integer, ForeignKey("ipv.instruments.instrument_id"), nullable=False)
    # instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    trader_id = Column(String(50), nullable=False)
    submitted_price = Column(Numeric(20, 8), nullable=False)
    position_quantity = Column(Numeric(20, 4), nullable=False)
    valuation_date = Column(Date, nullable=False)
    submission_ts = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_system = Column(String(100), nullable=False, default="QUARTZ")
    status = Column(String(20), nullable=False, default="PENDING")

    instrument = relationship("Instrument", back_populates="valuations")
    ipv_result = relationship("IPVResult", back_populates="valuation", uselist=False)

    def to_dict(self) -> dict:
        return {
            "valuation_id": self.valuation_id,
            "instrument_id": self.instrument_id,
            "ticker": self.instrument.ticker if self.instrument else None,
            "trader_id": self.trader_id,
            "submitted_price": float(self.submitted_price),
            "position_quantity": float(self.position_quantity),
            "valuation_date": self.valuation_date.isoformat(),
            "submission_ts": self.submission_ts.isoformat(),
            "source_system": self.source_system,
            "status": self.status
        }


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = {"schema": "ipv"}
    # __table_args__ = {}

    price_id = Column(
        Integer,
        Sequence("market_prices_seq", schema="ipv"),
        primary_key=True
    )
    instrument_id = Column(Integer, ForeignKey("ipv.instruments.instrument_id"), nullable=False)
    # instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    price_source = Column(String(100), nullable=False)
    market_price = Column(Numeric(20, 8), nullable=False)
    price_date = Column(Date, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_stale = Column(SmallInteger, nullable=False, default=0)

    instrument = relationship("Instrument", back_populates="market_prices")

    def to_dict(self) -> dict:
        return {
            "price_id": self.price_id,
            "instrument_id": self.instrument_id,
            "ticker": self.instrument.ticker if self.instrument else None,
            "price_source": self.price_source,
            "market_price": float(self.market_price),
            "price_date": self.price_date.isoformat(),
            "ingested_at": self.ingested_at.isoformat(),
            "is_stale": bool(self.is_stale)
        }


class IPVResult(Base):
    __tablename__ = "ipv_results"
    __table_args__ = {"schema": "ipv"}
    # __table_args__ = {}

    result_id = Column(
        Integer,
        Sequence("ipv_results_seq", schema="ipv"),
        primary_key=True
    )
    valuation_id = Column(Integer, ForeignKey("ipv.trader_valuations.valuation_id"), nullable=False)
    market_price_id = Column(Integer, ForeignKey("ipv.market_prices.price_id"), nullable=False)
    # valuation_id = Column(Integer, ForeignKey("trader_valuations.valuation_id"), nullable=False)
    # market_price_id = Column(Integer, ForeignKey("market_prices.price_id"), nullable=False)
    trader_price = Column(Numeric(20, 8), nullable=False)
    independent_price = Column(Numeric(20, 8), nullable=False)
    variance_abs = Column(Numeric(20, 8), nullable=False)
    variance_pct = Column(Numeric(10, 6), nullable=False)
    breach_flag = Column(SmallInteger, nullable=False, default=0)
    threshold_pct = Column(Numeric(10, 6), nullable=False)
    reconciled_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_by = Column(String(50))
    review_notes = Column(String(500))

    valuation = relationship("TraderValuation", back_populates="ipv_result")
    market_price = relationship("MarketPrice")

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "valuation_id": self.valuation_id,
            "market_price_id": self.market_price_id,
            "trader_price": float(self.trader_price),
            "independent_price": float(self.independent_price),
            "variance_abs": float(self.variance_abs),
            "variance_pct": float(self.variance_pct),
            "breach_flag": bool(self.breach_flag),
            "threshold_pct": float(self.threshold_pct),
            "reconciled_at": self.reconciled_at.isoformat(),
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes
        }
