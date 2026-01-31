# Database Schema Reference 🗄️

Sentinel uses a hybrid storage approach:

- **PostgreSQL**: Persistent storage for historical data and AI audit logs.
- **Redis**: High-speed caching for real-time dashboard feeds.

---

## 🐘 PostgreSQL Schema

### 1. `materials`

Master list of tracked commodities.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Unique ID |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | e.g., 'Copper', 'PVC' |
| `category` | VARCHAR(50) | NOT NULL | 'Shielding', 'Polymer' |
| `lead_time` | INT | DEFAULT 30 | Procurement lead time in days |

### 2. `countries`

Master list of operational regions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Unique ID |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | e.g., 'Egypt', 'Germany' |
| `code` | VARCHAR(10) | UNIQUE | UN Comtrade or ISO Code |

### 3. `market_prices`

Raw chronological price feeds (Data Layer 1).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Input ID |
| `material_id` | INT | FK -> materials.id | Linked Material |
| `price` | DECIMAL(10,2) | NOT NULL | Market Value |
| `currency` | VARCHAR(10) | DEFAULT 'USD' | Currency |
| `source` | VARCHAR(50) | | e.g., 'Yahoo', 'LME' |
| `captured_at` | TIMESTAMP | DEFAULT NOW() | Ingestion Time |

### 4. `ai_signals`

AI-generated forecasts and decisions (Data Layer 2).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | SERIAL | PK | Prediction ID |
| `material_id` | INT | FK -> materials.id | Linked Material |
| `country_id` | INT | FK -> countries.id | Linked Country context |
| `input_price` | DECIMAL(10,2) | NOT NULL | Price at time of inference |
| `decision` | VARCHAR(20) | NOT NULL | 'BUY', 'WAIT', 'HOLD' |
| `confidence_score` | DECIMAL(5,2) | | 0-100 Confidence Metric |
| `stockout_risk` | DECIMAL(5,4) | | 0.0-1.0 Risk Probability |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Inference Time |

---

## ⚡ Redis Key Schema

Sentinel uses Redis for the "Live Feed" mechanism.

### Key Pattern: `live:{Country}:{Material}:{Metric}`

Stores specific metrics for the worker processing loop.

| Key Example | Standard Value | Description |
| :--- | :--- | :--- |
| `live:Egypt:Copper:price` | `9000.50` | Latest processed price. |
| `live:Egypt:Copper:signal` | `BUY` | Latest decision. |
| `live:Egypt:Copper:risk` | `0.15` | Risk factor. |

### Key Pattern: `live:{Material}` (Hash)

Aggregated global view for the Dashboard.

| Field | Example |
| :--- | :--- |
| `price` | `9000.50` |
| `decision` | `BUY` |
| `trend` | `1.5` |
| `updated_at` | `1706691234` |
