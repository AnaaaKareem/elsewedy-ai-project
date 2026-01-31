# Sentinel Dashboard Design Specification

**Theme:** Hyper-Glass / Deep Space Command Center
**Version:** 1.0

---

## 1. Design Philosophy

The interface is designed to emulate a **"Futuristic Command Center"**. It prioritizes data density, dark mode aesthetics, and immediate visual cues (Red/Green signals).

### Visual Language

* **Palette:**
  * **Background:** Deep Space Black (`#09090b` / Zinc-950) with "Aurora" mesh gradients.
  * **Glass (`glass-panel`):** Heavy blur (`backdrop-blur-xl`), low opacity white (`bg-white/5`), iridescent borders (`border-white/10`).
  * **Accents:**
    * **Signal Green:** `#10b981` (Emerald-500) for "Buy" signals.
    * **Alert Red:** `#ef4444` (Red-500) for "Wait" or supply shocks.
    * **Neon Violet:** `#8b5cf6` (Violet-500) for AI confidence indicators.
* **Typography:** `Inter` (Sans-serif), tracking-wide for headers, tabular nums for data.

---

## 2. Layout Structure

The application uses a **Shell Layout** with a fixed sidebar and a scrollable main grid.

### A. The Shell (`Shell.tsx`)

* **Sidebar (Left):** Navigation icons (Dashboard, Inventory, Alerts, Settings). Glassmorphism rail.
* **Top Bar:** "Sentinel AI" Logo, Global Status (System Health), User Profile.
* **Main Content Area:** 12-Column Grid System using CSS Grid.

### B. The Grid (`page.tsx`)

* **Row 1: The "Heads-Up" Display (HUD):**
  * **Global Map (7 cols):** 3D Globe showing active supply routes and "Hot Zones".
  * **Scanner Feed (5 cols):** Live ticker of incoming market events (API calls).
* **Row 2: Material Intelligence Deck:**
  * **Metric Cards:** A grid of cards for each tracked material (Copper, Aluminum, PVC).

---

## 3. Core Components

### 1. `Globe.tsx` (Map Visualization)

* **Tech:** `react-leaflet`, `leaflet`.
* **Style:** Custom dark-mode tiles (`CartoDB.DarkMatter`).
* **Features:**
  * Pulsing markers at origin countries (e.g., Chile, Egypt).
  * Polylines connecting Suppliers -> Factories.
  * Tooltips showing real-time lead time risks.

### 2. `MetricCard.tsx`

* **Visual:** `GlassCard` container.
* **Content:**
  * **Header:** Material Name (e.g., "Copper Cathodes").
  * **Main Stat:** Live Price (e.g., "$9,250").
  * **Trend:** Sparkline or % Change indicator.
  * **AI Signal:** Large Badge ("BUY NOW" / "WAIT").
  * **Confidence:** Radial progress bar (e.g., "89% Conf").

### 3. `GlassCard.tsx` (Primitive)

* **Props:** `variant` (default, heavy), `hover` (boolean).
* **CSS:**

    ```css
    .glass-card {
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.05);
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    ```

---

## 4. User Experience (UX) Flow

1. **Monitoring (Passive):**
    * User views the "Command Center".
    * Map shows green lines (healthy routes).
    * Cards show steady prices.
2. **Alert (Active):**
    * **Event:** Red Sea logistics issue detected by AI.
    * **UI:** Map route turns Red. "Copper" card flashes "Alert".
    * **Notification:** Toast message appears: "Lead Time Risk Detected".
3. **Decision:**
    * User clicks "Copper" card.
    * Drills down into **Detail View** (History, Forecast).
    * AI recommends: "Increase Safety Stock by 15%".

---

## 5. Technology Stack (Frontend)

* **Framework:** Next.js 14 (App Router).
* **Styling:** Tailwind CSS + CSS Variables.
* **State:** React Server Components (RSC) for initial data, SWR/TanStack Query for live polling.
* **Charts:** Recharts or Tremor.
* **Maps:** React-Leaflet.
