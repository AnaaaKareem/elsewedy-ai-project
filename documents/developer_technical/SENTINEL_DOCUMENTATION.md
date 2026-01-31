# Elsewedy Sentinel - Master Project Documentation

**Version:** 2.0 (Consolidated)
**Last Updated:** December 31, 2025

---

## 1. Project Overview

**Sentinel** is an intelligent Supply Chain Intelligence platform designed for Elsewedy Electric (and the broader cable industry). It shifts procurement from reactive "spot buying" to proactive "strategic sourcing" by predicting raw material prices and bridging the gap between global market signals (LME, Oil, ForEx) and local operational realities.

### Core Objectives

1. **Cost Reduction:** Buy materials when prices are forecasted to dip.
2. **Risk Mitigation:** Identifying supply shocks (e.g., Red Sea logistics issues) before they impact production.
3. **Inventory Optimization:** Dynamically adjusting safety stock based on lead-time risks.

### Key Differentiators

* **Hyper-Local + Global:** Unlike generic forecasters (Bloomberg), Sentinel combines global indices ($Oil, $Copper) with local constraints (EGP/USD rate, Egyptian Customs clearance times).
* **Cable-Specific Logic:** It understands "Shielding" vs "Insulation" vs "Conductor" materials, not just generic commodities.
* **Hyper-Local + Global:** Unlike generic forecasters (Bloomberg), Sentinel combines global indices ($Oil, $Copper) with local constraints (EGP/USD rate, Egyptian Customs clearance times).
* **Cable-Specific Logic:** It understands "Shielding" vs "Insulation" vs "Conductor" materials, not just generic commodities.
* **Action-Oriented:** It doesn't just show a chart; it outputs a decision ("Buy Now", "Wait", "Hedge").

---

## 2. System Architecture & Scaling

The system uses an **Event-Driven Distributed Architecture** to handle **11 countries** and **8 raw material categories**.

### "Fan-Out" Ingestion Strategy

1. **Scheduler (The Conductor):** A lightweight service that *never* fetches data itself. It pushes "Jobs" to a Queue (RabbitMQ `ingestion_tasks`).
2. **Ingestion Workers (The Fetchers):** Stateless containers that listen to the queue and perform API calls (Yahoo Finance, LME, FRED). Scaling workers = Faster ingestion.
3. **Topic Exchange:** Data is routed via `sentinel_market_data` with keys like `region.country.category.material` (e.g., `mena.egypt.polymer.pvc`).

### Inference Worker Groups ("The Brain")

AI models are sharded by complexity:

* **Polymer Workers (`*.polymer.*`):** Run **XGBoost**. Fast, CPU-bound. Scaled to 2 replicas.
* **Shielding Workers (`*.shielding.*`):</b> Run **LSTM/DeepAR**. Slower, potentially GPU-bound. Scaled to 5 replicas.
* **Screening Workers (`*.screening.*`):** Run **Croston’s Method**. Very fast statistical logic. 1 replica.

### Disaster Recovery (DR) Strategy (Applied)

The following measures are active in the current deployment:

* **PostgreSQL:** Persistence via mapped volume (`sentinel_db_data`).
  * **Backup:** Automated via `scripts/backup_db.sh` (Manual trigger or Cron).
* **Redis:** AOF (Append-Only File) Persistence **Enabled**. Replays write log on container restart to prevent cache loss.
* **Vault:** Persistence via mapped volume. Unseal keys must be managed manually (3-of-5 rule) if running in Production mode.

---

## 3. AI Models & Methodology

Sentinel employs a "Ensemble of Experts" approach, selecting the best algorithm for the material type.

| Category | Model | Why? | Features |
| :--- | :--- | :--- | :--- |
| **Shielding** | **LSTM / DeepAR** | High-volume, daily data (Copper, Aluminum). Captures complex temporal dependencies. | Price history, LME Index, Oil Price. |
| **Polymer** | **XGBoost / CatBoost** | Driven by external factors (Oil price lag). Handles non-linear relationships well. | Oil Price (Lagged), Global Construction Index. |

### Training Strategy ("Pre-Flight")

To solve the "Cold Start" problem (new deployment has 0 database history):

1. **CSV Injection:** Historical data (2+ years) is exported to `sentinel_training_data.csv`.
2. **Offline Training:** A dedicated script (`offline_trainer.py`) trains models on this CSV during the build phase.
3. **Weight Baking:** Trained weights (`.pth`, `.json`) are baked into the Docker image, so the system is smart from Minute 0.

---

## 4. Data Extraction Schedule

| Source | Frequency | Data Points | Target |
| :--- | :--- | :--- | :--- |
| **LME / Yahoo** | Real-time (Stream) | Copper, Aluminum, Brent Oil | Shielding & Polymer Models |
| **FRED (St. Louis Fed)**| Daily | Global Construction Index, Inflation | Polymer (Macro drivers) |
| **Internal ERP** | Daily (Batch) | Inventory Levels, Production Plan | Constraint Logic |

---

## 5. Training Verification (Colab)

For verifying models outside the production environment (Google Colab):

1. **Generate Data:** Run `services/ai_engine/src/data_exporter.py` to get the CSV.
2. **Upload:** Load `sentinel_training_data.csv` to Colab.
3. **Run Workbook:** Execute `Sentinel_Training_Workbook.ipynb` to visualize:
    * RMSE/MAPE for Price predictions.
    * RMSE/MAPE for Price predictions.
    * Directional Accuracy (Did we predict the *trend* correctly?).

---

## 6. Operations & Maintenance

### Daily Routine

1. **Backup Database:** Run `./scripts/backup_db.sh` to snapshot the PostgreSQL state.
2. **Check Logs:** Monitor `docker-compose logs -f --tail=100` for `ERROR` signals from `sentinel_ai_engine`.

### Scaling

To increase ingestion throughput:

```bash
# Add more ingestion workers
docker-compose up -d --scale market_ingestion=3
```

### Emergency Restore

If the database container fails:

1. Stop containers: `docker-compose down`
2. Restore volume: `cat backups/db/dump_LATEST.sql | docker exec -i sentinel_db psql -U postgres`
3. Restart: `docker-compose up -d`

---

## 7. Data & Message Schema

### RabbitMQ Topology

The system uses a **Dispatcher-Worker** pattern involving two durable queues:

1. **Queue:** `market_updates`
    * **Source:** `market_ingestion`
    * **Consumer:** `ai_engine` (Dispatcher Thread)
    * **Payload:** `{"material": "Copper", "price": 9200.50, "trend": "UP", "time": 1704067200}`

2. **Queue:** `prediction_tasks`
    * **Source:** `ai_engine` (Dispatcher Thread)
    * **Consumer:** `ai_engine` (Worker Thread)
    * **Payload:** `{"country_name": "Egypt", "country_code": "818", "material": "Copper", "price": 9200.50}`

### Redis Key Structure (Hot Cache)

Used for real-time dashboard state.
* `live:Egypt:Copper:price` (Float)
* `live:Egypt:Copper:signal` (String: "BUY", "WAIT")
* `live:Egypt:Copper:confidence` (Int: 0-100)

### PostgreSQL Schema (Cold Storage)

* **materials**: Registry of 8 raw materials and their lead times.
* **countries**: Registry of 11 active countries.
* **market_prices**: Historical tick data for model training.
* **ai_signals**: Audit log of every AI decision made, including confidence scores.
