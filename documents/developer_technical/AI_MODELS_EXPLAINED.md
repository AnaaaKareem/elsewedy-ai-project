# Sentinel AI Models Explained

This document details the three distinct AI models used by the Sentinel platform, each tailored to a specific class of material ("Pillar").

## 1. Shielding Materials (LSTM)

**Target**: Metals like Copper, Aluminum, Lead.
**Characteristic**: High price volatility, time-series dependency, driven by global exchanges (LME).

### Architecture

* **Type**: Deep Learning (Recurrent Neural Network).
* **Algorithm**: Long Short-Term Memory (LSTM) or Gated Recurrent Unit (GRU).
* **Library**: `PyTorch`.
* **Structure**:
  * Input Layer: Accepts a sequence of normalized prices (default window: 60 days).
  * Hidden Layers: 2 Layers of 64 units each.
  * Output Layer: Single dense neuron (Linear) predicting the next normalized price.

### Data Processing

* **Normalization**: Min-Max scaling is applied to the input window to keep values between 0 and 1. This is crucial for LSTM convergence.
* **Windowing**: The model looks at a rolling window of the past 60 data points to predict the 61st.

### Why this model?

LSTMs are excellent at capturing "long-term dependencies" in time-series data, making them ideal for understanding cyclical trends in metal prices.

---

## 2. Polymer Materials (XGBoost)

**Target**: Oil derivatives like PVC, XLPE, PE.
**Characteristic**: Strong correlation with external macroeconomic factors (Oil prices).

### Architecture

* **Type**: Gradient Boosting Machine (GBM).
* **Algorithm**: XGBoost (Extreme Gradient Boosting) or LightGBM.
* **Library**: `xgboost` / `lightgbm`.
* **Parameters**:
  * Estimators: 1000 trees.
  * Max Depth: 6 (to capture interaction effects).
  * Learning Rate (Eta): 0.05.

### Features (Input)

Unlike the LSTM which looks at *time*, this model looks at *drivers*:

1. **Current Material Price** (e.g., PVC Spot).
2. **Oil Price** (Brent Crude - The primary feedstock cost driver).
3. **Construction Index** (Demand signal).
4. **FX Rate** (EGP/USD - specific to local procurement costs).

### Why this model?

Gradient Boosting is state-of-the-art for tabular data where the relationship between features (Oil -> PVC) is non-linear but stable.

---

## 3. Screening Materials (Croston’s Method)

**Target**: Specialty items like Mica Tape, Water-blocking Tape.
**Characteristic**: "Lumpy" or Intermittent Demand (irregular orders).

### Architecture

* **Type**: Statistical Forecasting.
* **Algorithm**: Croston’s Method (1972).
* **Library**: Custom Python implementation (`numpy`).

### Logic

Standard forecasting (like Moving Average) fails here because it averages the "zeros" (days with no orders) with the spikes, resulting in a constantly low forecast that causes stockouts when an order actually comes.

Croston's Method splits the problem into two:

1. **Demand Size**: "How much is ordered?" (Exponential Smoothing on non-zero values).
2. **Inter-Arrival Time**: "How often is it ordered?" (Exponential Smoothing on the time interval between non-zero values).

**Forecast = (Estimated Size) / (Estimated Interval)**

### Why this model?

It provides a robust safety stock baseline for items that are ordered infrequently but are critical to have on hand.
