# Why Sentinel? (Differentiation Statement)

While many systems offer basic "Demand Forecasting" (predicting X amount), Sentinel differs by being an **Autonomous Supply Chain Agent** that closes the loop between *Prediction*, *Strategy*, and *Action*.

## 1. Versus Standard ERPs (SAP/Oracle)

* **Standard ERP**: Static logic. "If stock < 100, buy 500." Reactive.
* **Sentinel**: Dynamic logic. "Oil prices are lagging, creating a 30-day window to buy Polymer cheap." Proactive.

## 2. Versus Generic AI Forecasting Tools

* **Others**: Black-box series forecasting. "Demand will be 500."
* **Sentinel**: **Structural Modeling**. It understands *why* demand moves (e.g., using "Reconciliation" to align country-level project spikes with global purchasing power).

## 3. Unique Architectural Features

* **Multi-Agent "Brains"**: We don't use one model. We use specialized agents:
  * **XGBoost Agent** for Oil-linked Polymers.
  * **LSTM Agent** for Volatile Metals (LME).
  * **Croston Agent** for Lumpy Specialty Tapes.
* **Inventory Optimization Layer**: We don't just predict demand; we solve for the **Optimal Buy Order** using Linear Programming, balancing Holding Costs vs. Price Surges.

## 4. Business Impact

* **Resilience**: Detects supply chain shocks (e.g., Red Sea shipping delays impact LME prices) before they hit production.
* **Cost Efficiency**: Moves from "Just-in-Time" to "Just-in-Case" (Strategic Stockpiling) when algorithms detect an arbitrage opportunity.

**Summary**: Sentinel is not just a dashboard; it is an **Intelligence Layer** that sits above your ERP to turn Data into Profit.
