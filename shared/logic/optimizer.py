from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value

"""
Optimization Layer for Sentinel.

This module is responsible for the Prescriptive Analytics phase (Layer 4).
It uses Linear Programming (via PuLP) to determine the optimal procurement strategy
given a demand forecast and predicted price trends, balancing purchasing costs
against holding costs and safety stock requirements.
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
    def __init__(self, material_name, lead_time_days, holding_cost_pct=0.02):
        """
        Initialize the SentinelOptimizer.

        Args:
            material_name (str): The name of the material.
            lead_time_days (int): The supply lead time in days.
            holding_cost_pct (float, optional): Cost to hold one unit of stock per day 
                                              as a fraction of price. Defaults to 0.02 (2%).
        """
        self.material = material_name
        self.lead_time = lead_time_days
        self.holding_cost_pct = holding_cost_pct

    def optimize_procurement(self, forecast_demand, predicted_prices, current_stock):
        """
        Solves for the minimum cost purchasing schedule using Linear Programming.

        The problem is modeled as:
        Minimize Sum(Buy_t * P_t + Stock_t * P_t * h)
        Subject to:
          - Inventory Balance: Stock_t = Stock_{t-1} + Buy_t - Demand_t
          - Safety Stock: Stock_t >= Safety_Buffer

        Args:
            forecast_demand (list[float]): List of predicted demand values for each period.
            predicted_prices (list[float]): List of predicted unit prices for each period.
            current_stock (float): Starting inventory level.

        Returns:
            dict: A dictionary mapping period index to the optimal buy quantity.
        """
        periods = range(len(forecast_demand))
        
        # Initialize the LP Problem structure (Minimization)
        prob = LpProblem(f"Optimize_{self.material}", LpMinimize)

        # Decision Variables
        # Buy[t]: Quantity to purchase in period t
        buy = LpVariable.dicts("Buy", periods, lowBound=0)
        # Stock[t]: Quantity held in inventory at the END of period t
        inventory = LpVariable.dicts("Stock", periods, lowBound=0)

        # Objective Function: Minimize (Purchase Cost + Holding Cost)
        # We sum costs over all periods in the horizon
        prob += lpSum([
            buy[t] * predicted_prices[t] + 
            inventory[t] * (predicted_prices[t] * self.holding_cost_pct)
            for t in periods
        ])

        # Constraints
        for t in periods:
            # Inventory Balance Constraint
            # Stock at end of t = Stock at end of t-1 (or initial) + Net Change
            if t == 0:
                prob += inventory[t] == current_stock + buy[t] - forecast_demand[t]
            else:
                prob += inventory[t] == inventory[t-1] + buy[t] - forecast_demand[t]

            # Safety Stock Constraint: Prevent stockouts
            # Ensure we always hold a buffer. Here defined as 50% of average demand.
            # This is critical for Pillar 3 ("Specialty Items") resilience.
            avg_demand = sum(forecast_demand) / len(forecast_demand)
            prob += inventory[t] >= avg_demand * 0.5 

        # Solve the linear problem
        prob.solve()

        # Extract results into a clean dictionary
        return {t: buy[t].varValue for t in periods}