# Elsewedy Sentinel 🛡️

**AI-Driven Supply Chain Intelligence & Procurement Optimization**

Sentinel is an advanced decision-support system designed to optimize the procurement of cable manufacturing materials (Polymers, Shielding, Screening). It leverages AI to track global market trends, predict price movements, and recommend optimal purchasing strategies.

---

## 🚀 Quick Start

The fastest way to get the system running is using the helper script:

```bash
# 1. Create your environment file
cp .env.example .env  # (Or create one based on DEPLOYMENT.md)

# 2. Launch the platform
./start.sh
```

Once running, access the dashboard at: **[http://localhost:3000](http://localhost:3000)**

---

## 📚 Documentation Structure

We have comprehensive documentation available in the `documents/` directory, organized by audience:

### 1. Developer & Technical Documentation (System-Facing)

*Located in `documents/developer_technical/`*

| Guide | Description |
| :--- | :--- |
| **[Getting Started](documents/developer_technical/GETTING_STARTED.md)** | Step-by-step tutorial for new developers. |
| **[Deployment Guide](documents/developer_technical/DEPLOYMENT.md)** | Operations, Environment Variables, and Docker details. |
| **[System Architecture](documents/developer_technical/ARCHITECTURE.md)** | High-level design, data flow, and microservices breakdown. |
| **[API Reference](documents/developer_technical/API_REFERENCE.md)** | Dashboard HTTP API and RabbitMQ Event Schemas. |
| **[Database Schema](documents/developer_technical/DATABASE_SCHEMA.md)** | PostgreSQL tables and Redis key patterns. |
| **[Software Design (SDD)](documents/developer_technical/SDD.md)** | Detailed component design and patterns. |

### 2. User Documentation (End-User Facing)

*Located in `documents/user_documentation/`*

| Guide | Description |
| :--- | :--- |
| **[User Manual](documents/user_documentation/USER_MANUAL.md)** | Guide for Procurement Officers on reading the dashboard. |

### 3. Project & Process Documentation

*Located in `documents/project_process/`*

| Guide | Description |
| :--- | :--- |
| **[Requirements (SRS)](documents/project_process/SRS.md)** | Functional and Non-Functional Requirements. |

---

## 🏗️ Architecture Overview

Sentinel operates as a set of Dockerized microservices:

- **`ai_engine`**: The brain. Runs inference using XGBoost/LSTM models.
- **`market_ingestion`**: The eyes. Fetches real-time data from external APIs.
- **`dashboard`**: The face. FastAPI-based UI for visualizing trends and signals.
- **Infrastructure**: RabbitMQ (Messaging), Redis (Hot Cache), PostgreSQL (Cold Storage), Vault (Security).

For a deep dive, see **[ARCHITECTURE.md](documents/developer_technical/ARCHITECTURE.md)**.
