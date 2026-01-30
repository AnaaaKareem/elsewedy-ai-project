import numpy as np

class MonteCarloSimulator:
    """
    Stochastic Inventory Simulation Module.
    
    Performs 'What-If' analysis to estimate the probability of stockouts 
    given the inherent uncertainty in Lead Times.
    """
    
    def __init__(self, num_simulations=1000, seed=42):
        self.num_simulations = num_simulations
        self.rng = np.random.default_rng(seed)

    def run_simulation(self, current_stock, daily_demand_mean, daily_demand_std, lead_time_mean, lead_time_std=2.0):
        """
        Runs Monte Carlo simulations to calculate stockout risk and inventory scenarios.
        
        This stochastic method models the uncertainty in Supply (Lead Time) and Demand,
        providing a probabilistic view of inventory health.

        Args:
            current_stock (float): Current inventory level.
            daily_demand_mean (float): Average daily demand.
            daily_demand_std (float): Standard deviation of daily demand.
            lead_time_mean (float): Expected lead time in days.
            lead_time_std (float): Uncertainty in shipping time (Simulation of delays).

        Returns:
            dict: {
                "stockout_probability": float (0.0 to 1.0),
                "avg_ending_stock": float,
                "worst_case_stock": float (Stock level at 5th percentile)
            }
        """


        # 1. Simulate Lead Times for all runs
        # We sample N lead times (one for each future scenario)
        # Lead time cannot be negative, so we clip min at 1 day
        simulated_lead_times = self.rng.normal(lead_time_mean, lead_time_std, self.num_simulations)
        simulated_lead_times = np.maximum(simulated_lead_times, 1.0) # Clip

        stockouts = 0
        ending_stocks = []

        # 2. Vectorized Simulation (Simulating total usage over the lead time)
        
        for lt in simulated_lead_times:
            # Approximate Total Demand during Lead Time
            # Demand ~ Normal(DailyMean * LT, DailyStd * sqrt(LT))
            demand_mean_total = daily_demand_mean * lt
            demand_std_total = daily_demand_std * np.sqrt(lt)
            
            total_demand = self.rng.normal(demand_mean_total, demand_std_total)
            total_demand = max(0, total_demand) # Demand cannot be negative
            
            # Ending Stock = Start - Demand
            final_stock = current_stock - total_demand
            
            ending_stocks.append(final_stock)
            if final_stock < 0:
                stockouts += 1
        
        ending_stocks = np.array(ending_stocks)
        
        # 3. Calculate Metrics
        risk_pct = stockouts / self.num_simulations
        avg_stock = np.mean(ending_stocks)
        
        # Worst Case: The stock level in the bottom 5% of scenarios (Value at Risk equivalent)
        worst_case = np.percentile(ending_stocks, 5)

        return {
            "stockout_probability": round(risk_pct, 4),
            "avg_ending_stock": round(avg_stock, 2),
            "worst_case_stock": round(worst_case, 2)
        }
