# Software Requirements Specification (SRS) 📝

## 1. Introduction

### 1.1 Purpose

The Sentinel system is designed to provide automated, real-time procurement intelligence for cable manufacturing raw materials. It aims to replace manual market tracking with an AI-driven approach.

### 1.2 Scope

The system covers:

* Real-time price monitoring (market_ingestion).
* Price prediction and decision making (ai_engine).
* Procurement optimization (inventory logic).
* Visualization of data and decisions (dashboard).

## 2. Functional Requirements

### 2.1 Data Ingestion

* **FR-01**: The system MUST fetch market prices for defined materials (Copper, Aluminum, PVC, etc.) every 60 seconds.
* **FR-02**: The system MUST support multiple data sources types: Financial APIs (Yahoo), Economic Data (FRED), and Trade Data (Comtrade).
* **FR-03**: The system MUST handle API rate limits and connection failures gracefully without crashing.

### 2.2 AI Analysis

* **FR-04**: The system MUST select the appropriate AI model based on material category (Strategy/Factory Pattern).
* **FR-05**: The system MUST generate a 'BUY', 'WAIT', or 'HOLD' signal for every price update.
* **FR-06**: The system MUST calculate a confidence score (0-100) and stockout risk probability (0-1) for each prediction.

### 2.3 Optimization

* **FR-07**: The system MUST calculate the optimal purchase quantity based on current stock (simulated), predicted price, and lead time.

### 2.4 User Interface

* **FR-08**: The Dashboard MUST display a real-time feed of material cards with Price, Trend, and Decision.
* **FR-09**: The Dashboard MUST provide an interactive map allowing users to select Countries.
* **FR-10**: Selecting a country MUST display specific regional intelligence (Economic Health, Risk Level).

## 3. Non-Functional Requirements

### 3.1 Performance

* **NFR-01**: Dashboard updates MUST reflect real-time data with a latency of less than 200ms (via Redis).
* **NFR-02**: The system MUST support concurrent processing of updates for 50+ countries.

### 3.2 Security

* **NFR-03**: All external API keys and database credentials MUST be stored in HashiCorp Vault.
* **NFR-04**: Secrets MUST NOT be hardcoded in the source code or committed to version control.

### 3.3 Reliability

* **NFR-05**: The system MUST implement a persistent message queue (RabbitMQ) to ensure no market data is lost during processing spikes.
* **NFR-06**: Critical components (Inference, Ingestion) MUST restart automatically upon failure (Docker Restart Policy).
