import unittest
import numpy as np
from logic.simulator import MonteCarloSimulator

class TestMonteCarloSimulator(unittest.TestCase):
    def setUp(self):
        self.simulator = MonteCarloSimulator(num_simulations=500, seed=42)

    def test_zero_demand(self):
        """Test that zero demand results in zero risk."""
        result = self.simulator.run_simulation(
            current_stock=100,
            daily_demand_mean=0,
            daily_demand_std=0,
            lead_time_mean=10
        )
        self.assertEqual(result['stockout_probability'], 0.0)
        self.assertEqual(result['avg_ending_stock'], 100.0)

    def test_high_stock_low_risk(self):
        """Test that massive inventory results in near-zero risk."""
        # Stock = 1000, Demand = 10/day, Lead Time = 10 days. Expected usage ~100. Buffer = 900.
        result = self.simulator.run_simulation(
            current_stock=1000,
            daily_demand_mean=10,
            daily_demand_std=2,
            lead_time_mean=10,
            lead_time_std=1
        )
        self.assertLess(result['stockout_probability'], 0.01)

    def test_guaranteed_stockout(self):
        """Test that insufficient inventory results in 100% risk."""
        # Stock = 50, Demand = 10/day, Lead Time = 10 days. Expected usage ~100. Shortfall = 50.
        result = self.simulator.run_simulation(
            current_stock=50,
            daily_demand_mean=10,
            daily_demand_std=2,
            lead_time_mean=10,
            lead_time_std=1
        )
        self.assertGreater(result['stockout_probability'], 0.95)
        self.assertLess(result['avg_ending_stock'], 0) # Should be negative on average (unfulfilled demand)

    def test_uncertainty_spike(self):
        """Test that volatility increases risk even if averages look fine."""
        # Stock = 105, Demand = 10/day, Lead Time = 10 days. Expected usage = 100. Surplus = 5.
        # But High Volatility (Std=5) should cause some failures.
        result = self.simulator.run_simulation(
            current_stock=105,
            daily_demand_mean=10,
            daily_demand_std=5, # High Volatility
            lead_time_mean=10,
            lead_time_std=2
        )
        # We expect some risk, definitely not 0, definitely not 1.
        self.assertGreater(result['stockout_probability'], 0.10)
        self.assertLess(result['stockout_probability'], 0.90)

if __name__ == '__main__':
    unittest.main()
