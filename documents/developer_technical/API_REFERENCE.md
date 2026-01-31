# API & Event Reference 📡

## 🌐 Dashboard HTTP API

**Base URL**: `http://localhost:3000`

### 1. `GET /api/live`

Fetches a consolidated snapshot of all materials.

* **Returns**: JSON Object with live market data and recent AI signals.
* **Response Example**:

    ```json
    {
      "materials": [
        {
          "name": "Copper",
          "price": 8500.00,
          "decision": "BUY",
          "trend": 1.25,
          "risk": 0.1,
          "confidence": 95
        }
      ],
      "ai_signals": [...]
    }
    ```

### 2. `GET /api/country/{country_code}`

Fetches details for a specific country context.

* **Params**: `country_code` (e.g., `818` for Egypt).
* **Response Example**:

    ```json
    {
      "name": "Egypt",
      "economic_health": "Stable",
      "local_demand_index": 82.5,
      "risk_level": "Low"
    }
    ```

---

## 📨 RabbitMQ Event Types

Events are serialized as JSON strings.

### Exchange: `(Default)`

#### Queue: `market_updates`

**Publisher**: Market Ingestion Service
**Consumer**: AI Engine Dispatcher
**Payload**:

```json
{
  "material": "Copper",        // String: Material Name
  "price": 9005.50,            // Float: Current Price
  "trend": 0.015,              // Float: % Change
  "time": 1706690000.0         // Float: Epoch Timestamp
}
```

#### Queue: `prediction_tasks`

**Publisher**: AI Engine Dispatcher
**Consumer**: AI Engine Worker
**Payload**:

```json
{
  "country_name": "Egypt",     // String
  "country_code": "818",       // String
  "material": "Copper",        // String
  "price": 9005.50             // Float
}
```
