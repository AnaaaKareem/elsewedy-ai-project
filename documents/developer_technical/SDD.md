# Software Design Document (SDD) 📐

## 1. Introduction

The Sentinel platform is a distributed system designed to automate procurement decisions. This document details the software design choices, patterns, and component interactions.

## 2. Design Patterns

### 2.1 Factory Pattern (AI Models)

The system uses the **Factory Method** pattern to instantiate the correct AI model based on the material category. This allows for extensibility—new material types with different mathematical properties can be added without modifying the consumer code.

* **Class**: `ModelFactory` (`services/ai_engine/src/ai_models/model_factory.py`)
* **Mechanism**:
  * `Polymer` -> Returns `SentinelGBMModel` (XGBoost). Best for regression with external drivers (Oil).
  * `Shielding` -> Returns `SentinelDLModel` (LSTM). Best for time-series forecasting of volatile metals.
  * `Screening` -> Returns `SentinelLumpyModel` (Croston's). Best for intermittent demand.

### 2.2 Strategy Pattern (Core Logic)

The `UnifiedSentinel` class (`shared/data_sources/unified_sentinel.py`) acts as a strategy context, selecting the appropriate data fetcher (Yahoo-Adapter, FRED-Adapter) based on the material's configured `driver`.

### 2.3 Producer-Consumer (Event Loop)

The system relies on an asynchronous event loop via RabbitMQ.

* **Producer**: `MarketIngestion` polls data and fires and forgets.
* **Consumer**: `AIEngine` acts as a worker, processing tasks from the queue. This decouples the speed of ingestion (fast) from inference (slow).

## 3. Component Design

### 3.1 Data Layer (`shared/infrastructure`)

* **ORM**: SQLAlchemy is used for database abstraction.
* **Session Management**: `SessionLocal` ensures thread-safe database connections.
* **Models**:
  * `Material`: Metadata (Lead Time, Category).
  * `MarketPrice`: Time-series data.
  * `AISignal`: Audit log of decisions.

### 3.2 AI Engine (`services/ai_engine`)

* **Dispatcher Thread**: Lightweight. Consumes market updates, fans out tasks per country.
* **Worker Thread**: Heavy. Loads model weights (cached in RAM), runs inference, runs optimization.
* **Optimization**: Uses a `SentinelOptimizer` (Linear Programming) to calculate `Buy Quantity` based on `Prediction` vs `Current Stock` + `Lead Time`.

### 3.3 Dashboard (`services/dashboard`)

* **Architecture**: Server-Side Rendering (SSR) via Jinja2 + Client-Side Polling.
* **Data Access**: Direct Redis read for high-performance dashboard updates (sub-10ms latency).

## 4. Algorithms

### 4.1 Procurement Optimization

![Inventory Optimization Logic IO Diagram](assets/optimization_logic_diagram.png)
<!-- TODO: Generate using Prompt #4 in documents/project_process/DIAGRAM_PROMPTS.md -->

Users Linear Programming to minimize:
$$ Cost = (Price \times Qty) + (HoldingCost \times Qty) $$
Subject to:
$$ Stock + Qty > SafetyStock $$

### 4.2 Risk Analysis

Uses Monte Carlo simulation (Gaussian distribution) on the predicted price error residuals to estimate the probability of stockouts.
