
import pandas as pd
import numpy as np

# Load Data
CSV_PATH = 'services/ai_engine/src/sentinel_training_data.csv'
print(f"🔄 Loading {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

# Identify rows with 0 demand
zero_mask = df['Demand_Qty'] == 0
count = zero_mask.sum()

if count == 0:
    print("✅ No zero demand values found. Data is already populated.")
    exit(0)

print(f"⚠️ Found {count} rows with 0 demand. Simulating data...")

# Generate specific demand profiles based on Category
def generate_demand(row):
    # Base ranges (Tons per week/entry)
    if 'Polymer' in row['Category']:
        base = np.random.uniform(100, 500)
    elif 'Shielding' in row['Category']: # Metals
        base = np.random.uniform(500, 2000)
    else: # Specialty
        base = np.random.uniform(20, 100)
    
    # Add some seasonality/noise
    # We don't have a clean date parsed here efficiently in apply, so just use random variation
    # In a real scenario, we'd use month-based seasonality
    variation = np.random.uniform(0.8, 1.2)
    
    return int(base * variation)

# Apply generation only to zero rows
df.loc[zero_mask, 'Demand_Qty'] = df[zero_mask].apply(generate_demand, axis=1)

# Save back
df.to_csv(CSV_PATH, index=False)
print(f"✅ Simulation Complete. Updated {count} rows.")
print(df[['Material', 'Demand_Qty']].sample(5))
