-- init.sql

-- 1. Table for Raw Market Prices (The Producer feeds this)
CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY,
    material VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    source VARCHAR(50),
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by material and time
CREATE INDEX IF NOT EXISTS idx_market_prices_mat_time 
ON market_prices (material, captured_at DESC);


-- 2. Table for AI Signals & Decisions (The Worker feeds this)
CREATE TABLE IF NOT EXISTS ai_signals (
    id SERIAL PRIMARY KEY,
    material VARCHAR(50) NOT NULL,
    input_price DECIMAL(10, 2) NOT NULL,
    predicted_demand DECIMAL(10, 2),
    decision VARCHAR(20) NOT NULL, -- 'BUY', 'WAIT', 'HOLD'
    confidence_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for dashboard history queries
CREATE INDEX IF NOT EXISTS idx_ai_signals_mat_time 
ON ai_signals (material, created_at DESC);