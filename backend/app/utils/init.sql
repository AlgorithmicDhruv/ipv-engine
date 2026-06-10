-- Oracle-compatible schema conventions:
-- SEQUENCE instead of SERIAL/IDENTITY
-- Explicit schema prefix
-- VARCHAR2-equivalent sizing
-- No BOOLEAN (using SMALLINT 0/1 as Oracle does)

CREATE SCHEMA IF NOT EXISTS ipv;

-- Instruments reference table
CREATE SEQUENCE ipv.instruments_seq START 1 INCREMENT 1;

CREATE TABLE ipv.instruments (
    instrument_id   INTEGER DEFAULT nextval('ipv.instruments_seq') PRIMARY KEY,
    ticker          VARCHAR(20)  NOT NULL UNIQUE,
    description     VARCHAR(200) NOT NULL,
    asset_class     VARCHAR(50)  NOT NULL,  -- EQUITY, FX_FORWARD, IR_SWAP, BOND
    currency        VARCHAR(3)   NOT NULL,
    is_active       SMALLINT     NOT NULL DEFAULT 1,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Trader-submitted valuations
CREATE SEQUENCE ipv.valuations_seq START 1 INCREMENT 1;

CREATE TABLE ipv.trader_valuations (
    valuation_id        INTEGER DEFAULT nextval('ipv.valuations_seq') PRIMARY KEY,
    instrument_id       INTEGER      NOT NULL REFERENCES ipv.instruments(instrument_id),
    trader_id           VARCHAR(50)  NOT NULL,
    submitted_price     NUMERIC(20, 8) NOT NULL,
    position_quantity   NUMERIC(20, 4) NOT NULL,
    valuation_date      DATE         NOT NULL,
    submission_ts       TIMESTAMP    NOT NULL DEFAULT NOW(),
    source_system       VARCHAR(100) NOT NULL DEFAULT 'QUARTZ',
    status              VARCHAR(20)  NOT NULL DEFAULT 'PENDING'  -- PENDING, VERIFIED, BREACHED, OVERRIDDEN
);

-- Independent market prices (synced from Redis feed)
CREATE SEQUENCE ipv.market_prices_seq START 1 INCREMENT 1;

CREATE TABLE ipv.market_prices (
    price_id        INTEGER DEFAULT nextval('ipv.market_prices_seq') PRIMARY KEY,
    instrument_id   INTEGER        NOT NULL REFERENCES ipv.instruments(instrument_id),
    price_source    VARCHAR(100)   NOT NULL,  -- BLOOMBERG, REUTERS, MARKIT
    market_price    NUMERIC(20, 8) NOT NULL,
    price_date      DATE           NOT NULL,
    ingested_at     TIMESTAMP      NOT NULL DEFAULT NOW(),
    is_stale        SMALLINT       NOT NULL DEFAULT 0
);

-- IPV reconciliation results
CREATE SEQUENCE ipv.ipv_results_seq START 1 INCREMENT 1;

CREATE TABLE ipv.ipv_results (
    result_id           INTEGER DEFAULT nextval('ipv.ipv_results_seq') PRIMARY KEY,
    valuation_id        INTEGER        NOT NULL REFERENCES ipv.trader_valuations(valuation_id),
    market_price_id     INTEGER        NOT NULL REFERENCES ipv.market_prices(price_id),
    trader_price        NUMERIC(20, 8) NOT NULL,
    independent_price   NUMERIC(20, 8) NOT NULL,
    variance_abs        NUMERIC(20, 8) NOT NULL,
    variance_pct        NUMERIC(10, 6) NOT NULL,
    breach_flag         SMALLINT       NOT NULL DEFAULT 0,
    threshold_pct       NUMERIC(10, 6) NOT NULL,
    reconciled_at       TIMESTAMP      NOT NULL DEFAULT NOW(),
    reviewed_by         VARCHAR(50),
    review_notes        VARCHAR(500)
);

-- Indexes for common query patterns
CREATE INDEX idx_trader_valuations_instrument ON ipv.trader_valuations(instrument_id, valuation_date);
CREATE INDEX idx_trader_valuations_date ON ipv.trader_valuations(valuation_date);
CREATE INDEX idx_market_prices_instrument ON ipv.market_prices(instrument_id, price_date);
CREATE INDEX idx_ipv_results_breach ON ipv.ipv_results(breach_flag, reconciled_at);
CREATE INDEX idx_ipv_results_valuation ON ipv.ipv_results(valuation_id);

-- Seed instruments
INSERT INTO ipv.instruments (ticker, description, asset_class, currency) VALUES
    ('AAPL',       'Apple Inc Common Stock',               'EQUITY',     'USD'),
    ('MSFT',       'Microsoft Corporation Common Stock',   'EQUITY',     'USD'),
    ('EURUSD_3M',  'EUR/USD 3-Month FX Forward',           'FX_FORWARD', 'USD'),
    ('GBPUSD_6M',  'GBP/USD 6-Month FX Forward',           'FX_FORWARD', 'GBP'),
    ('US10Y_IRS',  'USD 10Y Interest Rate Swap',           'IR_SWAP',    'USD'),
    ('UST_2Y',     'US Treasury 2-Year Note',               'BOND',       'USD');
