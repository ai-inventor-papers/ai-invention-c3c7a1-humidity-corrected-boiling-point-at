#!/usr/bin/env python3
"""
Independent re-derivation of headline numbers from raw Forbes data.
This script uses a completely different code path than method.py to verify results.
"""

import json
import numpy as np
from scipy.stats import pearsonr

# Raw Forbes 1857 data (same as in method.py)
FORBES_DATA_RAW = [
    (20.79, 194.5), (20.79, 194.3), (22.40, 197.9), (22.67, 198.4),
    (23.15, 199.4), (23.35, 199.9), (23.89, 200.9), (23.93, 201.1),
    (24.02, 201.4), (24.01, 201.3), (25.14, 203.6), (25.35, 204.6),
    (26.17, 206.3), (26.57, 206.5), (26.79, 207.2), (27.05, 208.0),
    (27.67, 209.0)
]

INH_TO_KPA = 3.38639

# Independent thermodynamic model using Antoine equation coefficients for water
# Antoine equation: log10(P) = A - B/(C+T) where P in mmHg, T in C
# For water (1-100C): A=8.07131, B=1730.63, C=233.426
# But we need Clausius-Clapeyron approach for consistency

def to_si(press_in, temp_f):
    p_kpa = press_in * INH_TO_KPA
    t_c = (temp_f - 32.0) * 5.0 / 9.0
    return p_kpa, t_c

# Data in SI
data_si = [to_si(p, t) for p, t in FORBES_DATA_RAW]
p_kpa = np.array([d[0] for d in data_si])
t_c = np.array([d[1] for d in data_si])

# Independent Clausius-Clapeyron implementation (different from method.py)
# Using SAME parameters as method.py to verify matching results
LR_WATER = 5260.0  # L/R in K (same as method.py)
T0_K = 373.15  # K
P0_KPA = 101.325  # kPa

def clausius_clapeyron_independent(p_kpa):
    """Independent implementation using P in kPa, returns T in C"""
    # 1/T = 1/T0 - ln(P/P0) / (L/R)
    # T = 1 / (1/T0 - ln(P/P0) / LR) - 273.15
    if isinstance(p_kpa, np.ndarray):
        inv_t = 1.0/T0_K - np.log(p_kpa / P0_KPA) / LR_WATER
        inv_t = np.where(inv_t <= 0, np.nan, inv_t)
        return 1.0 / inv_t - 273.15
    else:
        inv_t = 1.0/T0_K - np.log(p_kpa / P0_KPA) / LR_WATER
        if inv_t <= 0:
            return np.nan
        return 1.0 / inv_t - 273.15

t_thermo_c = clausius_clapeyron_independent(p_kpa)

print("=== Independent Thermodynamic Model ===")
print(f"At 101.325 kPa (1 atm): {clausius_clapeyron_independent(101.325):.4f} C")
print(f"Pressure range: [{p_kpa.min():.2f}, {p_kpa.max():.2f}] kPa")
print(f"Temp range (thermo): [{t_thermo_c.min():.2f}, {t_thermo_c.max():.2f}] C")

# Compute errors
errors = t_thermo_c - t_c
rmse = np.sqrt(np.mean(errors**2))
mbe = np.mean(errors)
corr, p_val = pearsonr(t_thermo_c, t_c)

print(f"\n=== Metrics (ISA/Thermodynamic Model) ===")
print(f"RMSE: {rmse:.4f} C")
print(f"MBE: {mbe:.4f} C")
print(f"Pearson r: {corr:.6f}")
print(f"p-value: {p_val:.2e}")

# Kinetic model with zero heat flux (should equal thermodynamic)
kinetic_k = 0.01
kinetic_n = 0.25
hf_zero = 0.0
delta_t_zero = kinetic_k * (hf_zero ** kinetic_n)
t_kinetic_zero = t_thermo_c + delta_t_zero
errors_zero = t_kinetic_zero - t_c
rmse_zero = np.sqrt(np.mean(errors_zero**2))
mbe_zero = np.mean(errors_zero)
corr_zero, p_zero = pearsonr(t_kinetic_zero, t_c)

print(f"\n=== Metrics (Kinetic Model, HF=0) ===")
print(f"RMSE: {rmse_zero:.4f} C")
print(f"MBE: {mbe_zero:.4f} C")
print(f"Pearson r: {corr_zero:.6f}")

# Dissolved gas model (-0.1 C perturbation)
t_dissolved = t_thermo_c - 0.1
errors_dissolved = t_dissolved - t_c
rmse_dissolved = np.sqrt(np.mean(errors_dissolved**2))
mbe_dissolved = np.mean(errors_dissolved)
corr_dissolved, p_dissolved = pearsonr(t_dissolved, t_c)

print(f"\n=== Metrics (Dissolved Gas Model) ===")
print(f"RMSE: {rmse_dissolved:.4f} C")
print(f"MBE: {mbe_dissolved:.4f} C")
print(f"Pearson r: {corr_dissolved:.6f}")

# Local pressure model (linear approximation)
t_local = 100.0 + 0.05 * (p_kpa - 101.325)
errors_local = t_local - t_c
rmse_local = np.sqrt(np.mean(errors_local**2))
mbe_local = np.mean(errors_local)
corr_local, p_local = pearsonr(t_local, t_c)

print(f"\n=== Metrics (Local Pressure Model) ===")
print(f"RMSE: {rmse_local:.4f} C")
print(f"MBE: {mbe_local:.4f} C")
print(f"Pearson r: {corr_local:.6f}")

# Sensitivity study
heat_flux_values = np.logspace(3, 6, 34)
print(f"\n=== Sensitivity Study (first 5 points) ===")
for i, hf in enumerate(heat_flux_values[:5]):
    delta_t = kinetic_k * (hf ** kinetic_n)
    print(f"  HF={hf:.0f} W/m^2: ΔT={delta_t:.4f} C")

print(f"  HF={heat_flux_values[-1]:.0f} W/m^2: ΔT={kinetic_k * (heat_flux_values[-1] ** kinetic_n):.4f} C")

# Verify against saved results
print("\n=== Verification Against Saved Results ===")
with open('results/exp_gen_sol_out.json', 'r') as f:
    saved = json.load(f)

# Extract predictions from first dataset
dataset = saved['datasets'][0]
print(f"Dataset: {dataset['dataset']}, examples: {len(dataset['examples'])}")

# Reconstruct actual temps from output
actuals = []
preds = []
for ex in dataset['examples']:
    out = json.loads(ex['output'])
    actuals.append(out['actual_c'])
    preds.append(out['pred_isa_c'])

actuals = np.array(actuals)
preds = np.array(preds)

errors_saved = preds - actuals
rmse_saved = np.sqrt(np.mean(errors_saved**2))
mbe_saved = np.mean(errors_saved)
corr_saved, p_saved = pearsonr(preds, actuals)

print(f"RMSE from saved: {rmse_saved:.4f} C")
print(f"MBE from saved: {mbe_saved:.4f} C")
print(f"Pearson r from saved: {corr_saved:.6f}")

# Compare
print(f"\n=== Comparison ===")
print(f"RMSE match: {abs(rmse - rmse_saved) < 0.001}")
print(f"MBE match: {abs(mbe - mbe_saved) < 0.001}")
print(f"Corr match: {abs(corr - corr_saved) < 0.001}")

# Shuffled test (placebo check)
print("\n=== Shuffled/Placebo Test ===")
np.random.seed(42)
t_c_shuffled = np.random.permutation(t_c)
corr_shuffled, p_shuffled = pearsonr(t_thermo_c, t_c_shuffled)
print(f"Shuffled Pearson r: {corr_shuffled:.4f} (p={p_shuffled:.4f})")
print(f"Should be near zero and non-significant: {abs(corr_shuffled) < 0.3 and p_shuffled > 0.05}")

# Constant baseline test
print("\n=== Constant Baseline Test ===")
t_const = np.full_like(t_c, np.mean(t_c))
errors_const = t_const - t_c
rmse_const = np.sqrt(np.mean(errors_const**2))
print(f"Constant baseline RMSE: {rmse_const:.4f} C")
print(f"Our model RMSE ({rmse:.4f}) better than constant: {rmse < rmse_const}")

print("\n=== All Independent Checks Complete ===")