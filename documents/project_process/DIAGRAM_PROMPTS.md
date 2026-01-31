# Diagram Generation Prompts 🎨

**Target Tool**: Nano Banana Pro  
**Style Profile**: Minimalist Technical  
**Color Palette**: White Background (`#FFFFFF`), Black Lines/Text (`#000000`), Red Accents (`#FF0000`)

---

## 1. High-Level System Architecture

**Purpose**: For `ARCHITECTURE.md` and the Report Introduction. Shows the microservices layout.

**Diagram Description**:
A central Hub-and-Spoke diagram.

- **Center**: RabbitMQ (Message Broker).
- **Left**: External Data Sources (Cloud) connecting to "Ingestion Service" (Container).
- **Top**: "AI Engine" (Brain) consuming from RabbitMQ.
- **Right**: "Dashboard" (UI) reading from Redis (Cache).
- **Bottom**: PostgreSQL (Database) and Vault (Lock).

**Prompt**:
> A professional software architecture diagram on a pure white background. Minimalist black line art style. Central component is a message broker node labeled "RabbitMQ". Arrows flow from a cloud icon labeled "External Data" to a box labeled "Ingestion", then to the center. Another path goes from center to a brain-like circuit node labeled "AI Engine". A simplified dashboard screen icon labeled "Dashboard" connects to a fast-access cylinder labeled "Redis". Use sharp, thin black lines for connections. Highlight critical data paths and the "AI Engine" node with subtle deep red accents. No shading, flat 2D style, high contrast, technical schematic look.

---

## 2. The "3-Pillar" AI Strategy

**Purpose**: For `ARABCAB_COMPETITION_REPORT.md`. Explains the Model Factory logic.

**Diagram Description**:
A Flowchart / Decision Tree.

- **Root**: "Raw Material Input".
- **Branch 1 (Polymers)**: Goes to "XGBoost" icon (Tree structure). Feature: "Oil Price".
- **Branch 2 (Shielding)**: Goes to "LSTM" icon (Waveform). Feature: "Time Series".
- **Branch 3 (Screening)**: Goes to "Croston" icon (Sparse dots). Feature: "Intermittent".
- **Convergence**: All arrows obtain a "Price Forecast".

**Prompt**:
> A technical decision tree flowchart on a white background. Black geometric shapes. Top node labeled "Material Input" splits into three distinct paths. Path 1 labeled "Polymers" leads to a decision tree icon labeled "XGBoost" with red leaf nodes. Path 2 labeled "Metals" leads to a sine-wave graph icon labeled "LSTM" with a red trend line. Path 3 labeled "Specialty" leads to a scattered dot plot icon labeled "Croston". All three paths converge at the bottom into a target circle labeled "Forecast". Minimalist, clean data science aesthetic, black text, white void background, critical decision points highlighted in red.

---

## 3. Data Flow Pipeline

**Purpose**: For `DATA_FLOW.md`. visualizes the journey of a price point.

**Diagram Description**:
A Left-to-Right linear process pipeline.

1. **Ingest**: API Icon.
2. **Queue**: Buffer Icon.
3. **Process**: Gear/AI Chip Icon.
4. **Optimize**: Balance Scale Icon.
5. **Act**: "BUY" Signal Card.

**Prompt**:
> A linear horizontal process diagram on a white background. Five steps connected by black arrows. Step 1: An API cloud icon. Step 2: A buffer queue icon. Step 3: A microchip icon symbolizing processing. Step 4: A balance scale icon representing optimization. Step 5: A notification card icon displaying "BUY". The flow arrows are black. The "Process" chip and "BUY" card feature distinct red highlights. Ultra-clean, thin diagrammatic lines, architectural sketch style, high resolution.

---

## 4. Inventory Optimization Logic

**Purpose**: For `SDD.md`. Explains the Linear Programming inputs/outputs.

**Diagram Description**:
A Mathematical Input/Output diagram.

- **Inputs (Left)**: Forecast (Line Graph), Inventory (Bar Chart), Lead Time (Clock).
- **Function (Center)**: A Funnel or Matrix labeled "Linear Optimization".
- **Outputs (Right)**: "Order Quantity" (Box), "Safety Stock" (Shield).

**Prompt**:
> A conceptual input-process-output diagram on a white background. Left side: Three small icons arranged vertically (a line graph, a bar chart, a clock), all in black outline. These feed into a central large funnel shape labeled "Optimization Logic". Emerging from the right of the funnel is a shipping box icon labeled "Order Qty" and a shield icon labeled "Safety Stock". The funnel and the shield have specific red outline accents. Technical drawing style, precise geometry, black text, whitespace dominant.
