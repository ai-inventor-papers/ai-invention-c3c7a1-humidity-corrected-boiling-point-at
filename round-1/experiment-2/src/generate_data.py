import numpy as np
import pandas as pd
import json

def generate_data():
    np.random.seed(42)
    n_sites = 20
    altitudes = np.linspace(0, 5000, n_sites)
    
    # ISA constants
    P0 = 1013.25  # hPa
    T0 = 288.15   # K
    g = 9.80665
    R = 8.31446
    M = 0.0289644
    L = 0.0065
    
    data = []
    for h in altitudes:
        # Pressure at altitude using barometric formula
        # P = P0 * exp(-g*M*h / (R*T))
        P_isa = P0 * np.exp(-g * M * h / (R * T0))
        # Add some atmospheric variability (noise)
        P_measured = P_isa + np.random.normal(0, 3)
        P_measured = max(P_measured, 50)  # Minimum pressure
        
        # Boiling point using Clausius-Clapeyron relation
        # ln(P/P0) = -L_v/R_v * (1/T - 1/T0)
        # For water: L_v = 2257 kJ/kg, R_v = 0.4615 kJ/(kg*K)
        Lv = 2257.0  # kJ/kg
        Rv = 0.4615  # kJ/(kg*K)
        T_bp_K = 1 / (1/373.15 - (Rv/Lv) * np.log(P_measured / P0))
        T_b_base = T_bp_K - 273.15  # Convert to Celsius
        
        # Add Kinetic (superheat ~0.5-2°C) and Gas effects (~0.1-0.3°C) + measurement noise
        superheat = np.random.normal(0.5, 0.3)
        gas_effect = np.random.normal(0.1, 0.05)
        measurement_noise = np.random.normal(0, 0.2)
        T_b_measured = T_b_base + superheat + gas_effect + measurement_noise
        
        data.append({
            "site_id": f"site_{int(h)}",
            "altitude": float(h),
            "P_measured": float(P_measured),
            "boiling_point_measured": float(T_b_measured)
        })
    
    with open("field_data.json", "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    generate_data()
