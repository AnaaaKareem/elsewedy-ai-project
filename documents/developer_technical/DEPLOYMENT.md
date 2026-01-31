# Deployment & Operations Guide ⚙️

This document outlines how to deploy, configure, and operate the Sentinel platform.

## 🐳 Docker Architecture

The system is defined in `docker-compose.yml` and consists of the following services:

| Service | Container Name | Description | Build Path |
| :--- | :--- | :--- | :--- |
| **Market Ingestion** | `sentinel_ingestion` | Fetches API data, pushes to RabbitMQ. | `./services/market_ingestion` |
| **AI Engine** | `sentinel_ai_engine` | Consumes messages, runs inference, saves to DB. | `./services/ai_engine` |
| **Dashboard** | `sentinel_dashboard` | Web UI for visualization. | `./services/dashboard` |
| **Vault** | `sentinel_vault` | Secrets management. | `hashicorp/vault:latest` |
| **RabbitMQ** | `sentinel_mq` | Message Broker. | `rabbitmq:management-alpine` |
| **Redis** | `sentinel_redis` | Real-time Cache. | `redis:alpine` |
| **PostgreSQL** | `sentinel_db` | Persistent Database. | `postgres:15.14` |

---

## 🔑 Environment Variables

The system relies on a `.env` file in the root directory. **Do not commit this file.**

### Infrastructure Credentials

| Variable | Default (Dev) | Description |
| :--- | :--- | :--- |
| `RABBITMQ_USER` | `admin` | Admin user for RabbitMQ. |
| `RABBITMQ_PASS` | `passme123` | Password for RabbitMQ. |
| `DB_PASSWORD` | `passme123` | Password for PostgreSQL user `postgres`. |
| `REDIS_URL` | `redis://redis:6379` | Connection string for Redis. |

### External API Keys

These are required for `market_ingestion` to function correctly.

| Variable | Description |
| :--- | :--- |
| `FRED_API_KEY` | Key for Federal Reserve Economic Data. |
| `EIA_API_KEY` | Key for Energy Information Administration. |
| `COMTRADE_API_KEY` | Key for UN Comtrade Database. |

---

## 🔐 Vault Integration

We use HashiCorp Vault to securely inject secrets into the containers.

**Initialization Process (`start.sh`):**

1. The `vault` container starts.
2. The `vault_init` ephemeral container builds, mounting `services/vault_init.sh`.
3. `start.sh` executes, reading the `.env` file from the host and passing values to `vault_init`.
4. `vault_init` writes these secrets into Vault at startup.
5. Microservices (`ai_engine`, `ingestion`) wait for Vault to be ready before starting their main loop.

**Troubleshooting Vault:**
If services hang at startup, check if Vault is unsealed:

```bash
docker logs sentinel_vault
```

---

## 🛑 Stopping the System

To stop all containers:

```bash
docker-compose down
```

To stop and **remove volumes** (WARNING: Deletes DB data):

```bash
docker-compose down -v
```

## 🔄 Restarting a Single Service

If you modify code in `ai_engine`:

```bash
docker-compose restart ai_engine
# OR to rebuild
docker-compose up -d --build ai_engine
```
