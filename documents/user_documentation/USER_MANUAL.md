# User Manual 📖

## 1. Accessing the Dashboard

Open your web browser and navigate to: **[http://localhost:3000](http://localhost:3000)**

## 2. Dashboard Layout

The Sentinel Dashboard is divided into three main sections:

### 2.1 Regional Intel (Left Sidebar)

This panel displays strategic data for a specific country.

* **How to use**: Click on any country marker on the interactive map.
* **Metrics**:
  * **Economic Health**: Qualitative assessment (Robust, Stable, Volatile) based on AI confidence.
  * **risk Level**: Probability of supply chain disruption (Low, High).
  * **Active Projects**: Number of recent procurement signals generated for this region.

### 2.2 Global Map (Center)

* Visualizes the operational footprint.
* **Status Indicator**: Shows "SYSTEM ONLINE" when the backend is connected.

### 2.3 Market Pulse (Right Sidebar)

A real-time feed of material cards, updating automatically as new data arrives.

* **Material Name**: e.g., "Copper", "PVC".
* **Price**: Current market price (USD).
* **Trend**: Arrow indicating price movement ($\nearrow$, $\searrow$).
* **Decision**: The AI's recommendation:
  * 🟢 **BUY**: Price is predicted to rise. Stock up now.
  * 🔴 **WAIT**: Price is predicted to fall. Delay purchase.
  * 🟡 **HOLD**: Market is stable/uncertain. Maintain current inventory.

## 3. Interpreting Signals

| Signal | Action Required |
| :--- | :--- |
| **BUY** | Contact supplier immediately. High probability of price increase. |
| **WAIT** | Do not purchase. Prices are trending down. |
| **High Risk** | Even if price is low, supply chain disruption is likely. Consider alternative suppliers. |

## 4. Troubleshooting

* **"System Offline"**: If the status indicator is red, contact IT (Deployment Guide).
* **Stale Data**: If prices aren't updating, ensure the Market Ingestion service is running.
