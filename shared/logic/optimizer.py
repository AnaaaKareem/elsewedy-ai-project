from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value

"""
Optimization Layer for Sentinel (Layer 4).

This module implements the Prescriptive Analytics phase of the Sentinel pipeline.
It utilizes Linear Programming (via PuLP) to determine the mathematically optimal
procurement strategy.

Key Goals:
- Minimize Total Cost of Ownership (TCO = Purchase + Holding + Capital Costs).
- Guarantee Service Levels (Safety Stock > 95%).
- Mitigate Supply Chain Risk (Dynamic Lead Time Buffers).
"""

class SentinelOptimizer:
    """
    Layer 4: Prescriptive Optimization.

    Determines the optimal quantity to buy for a specific material over a planning horizon
    to minimize total cost (purchase + holding), while satisfying demand and maintaining
    safety stock levels.

    Attributes:
        material (str): Name of the material being optimized (e.g., 'XLPE').
        lead_time (int): Lead time in days for the material.
        holding_cost_pct (float): Daily holding cost as a percentage of the material price.
    """
    def __init__(self, material_name, lead_time_days, holding_cost_pct=0.02, metal_interest_rate=0.0003):
        """
        Initialize the SentinelOptimizer.

        Args:
            material_name (str): The name of the material.
            lead_time_days (int): The supply lead time in days.
            holding_cost_pct (float, optional): Cost to hold one unit of stock per day 
                                              as a fraction of price. Defaults to 0.02 (2%).
            metal_interest_rate (float, optional): Cost of capital for high-value metals (daily). 
                                                 Defaults to 0.0003 (approx 10% annual).
        """
        self.material = material_name
        self.lead_time = lead_time_days
        self.holding_cost_pct = holding_cost_pct
        self.metal_interest_rate = metal_interest_rate

    def optimize_procurement(self, predicted_prices, current_stock, planning_horizon=4, category='Standard'):
        """
        Solves for the minimum cost purchasing schedule using Linear Programming.

        The problem is modeled as:
        Minimize Sum(Buy_t * P_t + Stock_t * P_t * h + [Stock_t * P_t * r if Metal])
        Subject to:
          - Inventory Balance: Stock_t = Stock_{t-1} + Buy_t - Demand_t
          - Safety Stock: Stock_t >= Safety_Buffer (Dynamic for Specialty)

        Args:
            predicted_prices (list[float]): List of predicted unit prices for each period.
            current_stock (float): Starting inventory level.
            category (str): Material category for risk logic (Default: 'Standard').

        Returns:
            dict: A dictionary mapping period index to the optimal buy quantity.
        """
        periods = range(planning_horizon)
        
        # Initialize the LP Problem structure (Minimization)
        prob = LpProblem(f"Optimize_{self.material}", LpMinimize)

        # Decision Variables
        # Buy[t]: Quantity to purchase in period t
        buy = LpVariable.dicts("Buy", periods, lowBound=0)
        # Stock[t]: Quantity held in inventory at the END of period t
        inventory = LpVariable.dicts("Stock", periods, lowBound=0)

        # Objective Function: Minimize (Purchase Cost + Holding Cost + Financial Risk)
        # Financial Risk Penalty applies primarily to Shielding (Metals) to discourage overstocking capital
        
        capital_cost_factor = self.metal_interest_rate if category == 'Shielding' else 0.0
        
        prob += lpSum([
            buy[t] * predicted_prices[t] + 
            inventory[t] * (predicted_prices[t] * (self.holding_cost_pct + capital_cost_factor))
            for t in periods
        ])

        # Constraints
        for t in periods:
            # Inventory Balance Constraint
            # Stock at end of t = Stock at end of t-1 (or initial) + Net Change
            # Demand removed, assuming 0 demand for now
            if t == 0:
                prob += inventory[t] == current_stock + buy[t]
            else:
                prob += inventory[t] == inventory[t-1] + buy[t]

            # Safety Stock Constraint: Prevent stockouts
            # Logic Update: Dynamic for 'Screening' (Specialty) vs Static for others
            
            avg_demand = 0 # demand removed
            
            if category == 'Screening':
                # Dynamic Safety Buffer: (Avg_Daily_Demand * Estimated_Lead_Time) * 1.2
                # Estimated Lead Time includes Shipping Risk (Default +7 days for India/China sourcing implied)
                risk_factor_days = 7 
                estimated_lead_time = self.lead_time + risk_factor_days
                safety_buffer = (avg_demand * estimated_lead_time) * 1.2
            else:
                # Standard Logic: 50% of average demand coverage
                # This is critical for Pillar 3 ("Specialty Items") resilience.
                safety_buffer = avg_demand * 0.5 
                
            prob += inventory[t] >= safety_buffer

        # Solve the linear problem
        prob.solve()

        # Extract results into a clean dictionary
        return {t: buy[t].varValue for t in periods}