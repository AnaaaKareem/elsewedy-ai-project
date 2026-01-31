# Sentinel System Data Flow Architecture

![Data Flow Pipeline](assets/data_flow_pipeline.png)
<!-- TODO: Generate using Prompt #3 in documents/project_process/DIAGRAM_PROMPTS.md -->

This document outlines how data flows through the Sentinel platform, from initial collection to final decision output.

## 1. Data Collection

**Source**: `shared/data_sources/unified_sentinel.py`
**Service**: `market_ingestion`

The system collects data from multiple external sources using the `UnifiedSentinel` interface:

* **Yahoo Finance**: Real-time material prices (e.g., Copper, Aluminum, PVC).
* **FRED (Federal Reserve)**: Economic drivers (e.g., Oil Prices, Construction Spending).
* **UN Comtrade**: Trade statistics (Imports/Exports).

The **Market Ingestion Service** polls these sources every **60 seconds** and publishes updates to a **RabbitMQ** exchange (`market_updates`).

## 2. Data Processing

**Service**: `ai_engine`

The AI Engine consumes messages from RabbitMQ and processes them in a multi-stage pipeline:

### A. Dispatching

The **Dispatcher Thread** receives the global market update and "fans out" the work, creating specific prediction tasks for each tracked country (e.g., Egypt, KSA, Germany). These tasks are pushed to an internal `prediction_tasks` queue.

### B. AI Inference (Layer 2)

**Code**: `src/ai_models/model_factory.py`
The **Worker Thread** picks up a task and selects the appropriate AI model based on the material category:

* **Shielding (Metals)**: Uses **LSTM (Deep Learning)** to model time-series price volatility.
* **Polymer (Oil Derivatives)**: Uses **XGBoost** to correlate prices with external drivers like Oil.
* **Screening (Specialty)**: Uses **Croston’s Method** for intermittent/lumpy demand.

### C. Optimization (Layer 4)

**Code**: `shared/logic/optimizer.py`
The system uses **Linear Programming (PuLP)** to determine the optimal procurement quantity.

* **Goal**: Minimize Total Cost (Purchase Price + Holding Cost).
* **Constraints**: Must maintain Safety Stock and respect Inventory Balance.
* **Output**: A specific quantity to "BUY" or a decision to "WAIT".

### D. Risk Analysis

**Code**: `shared/logic/simulator.py`
A **Monte Carlo Simulation** runs 1000 scenarios to estimate the probability of a stockout during the lead time, given supply chain uncertainty. This generates a **Risk Score** (e.g., "15% chance of stockout").

## 3. System Output

**Storage**: `PostgreSQL` & `Redis`

The results are persisted in two locations:

1. **Cold Storage (PostgreSQL)**:
    * Table: `ai_signals`
    * Data: `material`, `country`, `price`, `decision` (BUY/WAIT), `timestamp`.
    * Purpose: Historical audit trail and long-term reporting.

2. **Hot Storage (Redis)**:
    * Keys: `live:{country}:{material}:price`, `...:signal`, `...:risk`.
    * Purpose: Real-time dashboards and immediate alerting.

3. **Logs**:
    * The service prints structured logs to the console:
        `🌍 [Egypt] Forecast 92.50 | Signal BUY | Risk 12.5% | Saved`
