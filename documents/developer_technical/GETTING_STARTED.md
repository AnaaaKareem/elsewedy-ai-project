# Getting Started with Sentinel 🚀

Welcome to the Sentinel project! This guide will help you set up your development environment and run the system locally.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Docker & Docker Compose**: The entire system runs in containers.
    * [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
2. **Generic Tools**: `git`, `make` (optional), `curl`.
3. **Python 3.10+**: For local script execution (optional, if running outside Docker).

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd Elsewedy
```

### 2. Configure Environment

The system requires API keys for external data sources (FRED, Yahoo Finance, etc.).

1. Create a `.env` file in the root directory.
2. Add the required keys (see **[Deployment Guide](DEPLOYMENT.md)** for the full list).

```bash
# Example .env snippet
FRED_API_KEY=your_key_here
RABBITMQ_USER=admin
RABBITMQ_PASS=securepass
DB_PASSWORD=securepass
```

### 3. Start the System

We provide a convenient startup script that handles permissions, builds images, and initializes secrets.

```bash
./start.sh
```

**What this script does:**

1. Checks if `.env` exists.
2. Runs `docker-compose up -d --build`.
3. Waits for services to stabilize.
4. Initializes HashiCorp Vault with secrets from your `.env`.

### 4. Verify Installation

Once the script finishes (`✅ Project IS LIVE!`), check the following:

* **Dashboard**: Open [http://localhost:3000](http://localhost:3000). You should see the login or main dashboard page.
* **RabbitMQ Management**: Open [http://localhost:15672](http://localhost:15672). Login with the credentials defined in your `.env` (Default: `admin` / `passme123`).
* **Logs**: Check the logs of the AI Engine to ensure it's connected.

    ```bash
    docker logs -f sentinel_ai_engine
    ```

## 🧪 Running Tests

To run the test suite inside the container:

```bash
docker exec -it sentinel_ai_engine python -m pytest shared/tests
```

## 📂 Project Structure

* `services/`: Source code for `ai_engine`, `dashboard`, `market_ingestion`.
* `shared/`: Common logic (`UnifiedSentinel`, `database`, `config`) shared across services.
* `documents/`: Detailed project documentation.
