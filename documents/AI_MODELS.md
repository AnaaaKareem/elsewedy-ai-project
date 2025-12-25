# AI Models & Decision Workflow

This document details the three distinct AI "Brains" used by Sentinel, explaining *why* they were chosen, *how* they work, and *what* happens after they speak.

---

## 1. Polymer Brain (XGBoost)

**Focus**: *Oil-Derivative Pricing (PVC, XLPE, PE)*
**Why**: Polymer prices are not random; they lag behind Brent Crude Oil prices by ~30-45 days. Gradient Boosted Trees (XGBoost) are excellent at finding these non-linear correlations between external "features" (Oil) and the target (Polymer Price).

| Feature | Description | Sample Value |
| :--- | :--- | :--- |
| **Current Price** | The spot price today | `$1,200 / ton` |
| **Oil Price (Lagged)** | Brent Crude Price 30 days ago | `$85 / barrel` |
| **Shipping Index** | Global Container Freight Index | `2,400 pts` |
| **Seasonality** | Month of the year (Construction season?) | `June (6)` |

### Training Process

1. **Data**: 5 years of historical weekly prices joined with FRED Oil data.
2. **Objective**: Minimize RMSE (Root Mean Square Error).
3. **Output**: A single regression float value representing the *predicted price* in T+30 days.

### Example

* **Input**: `[Price=$1200, Oil=$92, Month=6]`
* **Model Output**: `$1265.50` (Predicting a rise due to high oil).

---

## 2. Shielding Brain (LSTM / Deep Neural Net)

**Focus**: *Volatile Metals (Copper, Aluminum)*
**Why**: These markets are "Efficient Markets" with high volatility. Simple regression fails here. LSTM (Long Short-Term Memory) networks are designed to remember long-term trends (e.g., "Copper has been rising for 6 months") while reacting to short-term shocks.

| Feature | Description | Sample Value |
| :--- | :--- | :--- |
| **Sequence T-0** | Price Today | `$9,000` |
| **Sequence T-1** | Price Yesterday | `$8,950` |
| **Sequence T-2** | Price 2 Days Ago | `$8,800` |
| **Sequence T-4** | Price 4 Days Ago | `$9,100` |
| **LME Inventory** | Global warehouse stock levels | `50,000 tons` |

### Training Process

1. **Data**: 10 years of daily LME closing prices.
2. **Technique**: Sliding Window (Values `t-0` to `t-9` predict `t+1`).
3. **Output**: Two values:
    * **Price**: `$9,050`
    * **Confidence**: `0.85` (How sure is the model?)

### Example

* **Input**: `[8800, 8900, 9000, 9100, 9000]` (Volatile but upward trend)
* **Model Output**: `$8,950` (Predicting a mean-reversion correction).

---

## 3. Screening Brain (Croston's Method)

**Focus**: *Intermittent "Lumpy" Demand (Mica Tape, Water-blocking Tape)*
**Why**: You don't buy these every day. Demand is "Zero, Zero, Zero, HUGE ORDER, Zero". Standard AI sees the zeros and predicts "Zero". Croston's Method separates the problem into two: *Risk of Order* and *Size of Order*.

| Feature | Description | Sample Value |
| :--- | :--- | :--- |
| **Inter-Arrival Time** | Days since last order | `45 days` |
| **Last Order Qty** | Size of the last actual order | `500 rolls` |
| **Current Stock** | Inventory level | `20 rolls` |

### Training Process

1. **Data**: Internal ERP Order History.
2. **Logic**: Calculates two averages:
    * Average Interval ($P$): "Orders happen every ~60 days".
    * Average Size ($Z$): "Average order is 1000 units".
3. **Output**: A risk score. "We are in the Danger Zone (Day 59 of 60)".

### Example

* **State**: Last order was 55 days ago. Avg Interval is 60.
* **Model Output**: `Risk: HIGH` (Expect order in 5 days). `Qty: 1000`.

---

## 4. The "Entire Process" (After Output)

So the model says "Copper will be $9,000". What happens next?

This is where the **Optimizer (Layer 4)** takes over. It uses the prediction as just *one input* in a Linear Programming equation.

### The Equation

$$ Minimize Cost = (Price \times Qty) + (Holding Cost \times Inventory) $$

**Constraints**:

1. **Inventory > Safety Stock**: Did the Croston model say a big order is coming? If yes, Safety Stock requirement shoots up.
2. **Lead Time**: If we order Copper now, it arrives in 30 days. Is the predicted price for *today* or *delivery day*? (We use delivery day).

### The Decision Logic

The `SentinelOptimizer` runs the math and outputs a specific instruction:

1. **IF** (Predicted Price is Rising) **AND** (Inventory is Low):
    * **Action**: `BUY 5,000 units NOW`.
    * *Reason*: "Buy now to beat the price hike."

2. **IF** (Predicted Price is Falling) **AND** (Inventory is OK):
    * **Action**: `WAIT`.
    * *Reason*: "Wait for the price to drop further. We have enough stock."

3. **IF** (Price is Rising) **AND** (Inventory is Full):
    * **Action**: `Differs by Policy`.
    * Option A (Aggressive): `BUY`. (Strategic stockpiling / Hedging).
    * Option B (Conservative): `HOLD`. (Don't increase holding costs).

### Final Execution

1. **Dashboard**: The `BUY` signal turns **GREEN** on the UI.
2. **Notification**: An email/Slack alert is sent to propercurement.
3. **ERP Sync**: (Optional) A Purchase Requisition is drafted in SAP/Oracle.
