-- init.sql

-- 1. Master Tables (Foreign Keys)
CREATE TABLE IF NOT EXISTS materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    lead_time INT DEFAULT 30
);

CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    code VARCHAR(10) UNIQUE -- ISO or Trade Code
);

-- Seed Initial Data (Idempotent)
INSERT INTO materials (name, category) VALUES 
('Copper', 'Shielding'), ('Aluminum', 'Shielding'), ('PVC', 'Polymer'), ('XLPE', 'Polymer'),
('PE', 'Polymer'), ('LSF', 'Polymer'), ('GSW', 'Shielding'), ('Copper Tape', 'Shielding'),
('Aluminum Tape', 'Shielding'), ('Mica Tape', 'Screening'), ('Water-blocking', 'Screening')
ON CONFLICT (name) DO NOTHING;

INSERT INTO countries (name, code) VALUES 
-- MENA
('Egypt', '818'), ('UAE', '784'), ('Saudi Arabia', '682'),
-- APAC
('China', '156'), ('India', '356'), ('Japan', '392'), ('S.Korea', '410'), ('Australia', '36'),
-- EU
('Germany', '276'), ('Italy', '380'), ('France', '251'), ('Spain', '724'), ('UK', '826'),
-- NA
('USA', '842'), ('Canada', '124'),
-- LATAM
('Brazil', '76'), ('Mexico', '484'), ('Argentina', '32'),
-- SSA
('South Africa', '710'), ('Nigeria', '566'), ('Kenya', '404')
ON CONFLICT (name) DO NOTHING;

-- 2. Table for Raw Market Prices (The Producer feeds this)
CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY,
    material_id INT REFERENCES materials(id), -- FK
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    source VARCHAR(50),
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_prices_mat_time 
ON market_prices (material_id, captured_at DESC);

-- 3. Table for AI Signals & Decisions (The Worker feeds this)
CREATE TABLE IF NOT EXISTS ai_signals (
    id SERIAL PRIMARY KEY,
    material_id INT REFERENCES materials(id), -- FK
    country_id INT REFERENCES countries(id),  -- FK
    input_price DECIMAL(10, 2) NOT NULL,
    predicted_demand DECIMAL(10, 2),
    decision VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_signals_mat_time 
ON ai_signals (material_id, created_at DESC);