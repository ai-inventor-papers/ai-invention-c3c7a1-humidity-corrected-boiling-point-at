#!/usr/bin/env python3
"""
Boiling Point Model Comparison Experiment

Compares three models against field measurements:
1. ISA Baseline - International Standard Atmosphere model
2. Kinetic Effect Model - Accounts for superheat from heat flux
3. Dissolved Gas Model - Accounts for dissolved gas depression

Uses local measured pressure as common input to control for synoptic weather confounders.
"""

import numpy as np
import json
from pathlib import Path
from loguru import logger


# Physical constants
P0 = 1013.25  # Standard pressure at sea level (hPa)
T0_K = 288.15  # Standard temperature at sea level (K)
g = 9.80665  # Gravitational acceleration (m/s^2)
R = 8.31446  # Universal gas constant (J/(mol*K))
M = 0.0289644  # Molar mass of dry air (kg/mol)
Lv = 2257.0  # Latent heat of vaporization of water (kJ/kg)
Rv = 0.4615  # Gas constant for water vapor (kJ/(kg*K))
T_bp0_K = 373.15  # Boiling point at standard pressure (K)


def load_field_data(filepath: str) -> list[dict]:
    """Load field measurement dataset."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} sites from {filepath}")
    return data


def isa_pressure(altitude: float) -> float:
    """Calculate ISA pressure at given altitude using barometric formula."""
    return P0 * np.exp(-g * M * altitude / (R * T0_K))


def boiling_point_from_pressure(pressure: float) -> float:
    """
    Calculate boiling point (Celsius) from pressure using Clausius-Clapeyron relation.
    ln(P/P0) = -Lv/Rv * (1/T - 1/T0)
    """
    if pressure <= 0:
        return np.nan
    T_K = 1 / (1/T_bp0_K - (Rv/Lv) * np.log(pressure / P0))
    return T_K - 273.15


def isa_model(altitude: float) -> float:
    """ISA baseline model: uses ISA pressure at altitude, not measured pressure."""
    P_isa = isa_pressure(altitude)
    return boiling_point_from_pressure(P_isa)


def isa_model_measured_pressure(pressure: float) -> float:
    """ISA physics model using measured pressure as input (fair comparison)."""
    return boiling_point_from_pressure(pressure)


def kinetic_model(pressure: float, heat_flux: float = 5000.0, vessel_diameter: float = 0.1) -> float:
    """
    Kinetic Effect Model: Accounts for superheat required for nucleation.
    
    Superheat ΔT_superheat ≈ (2σT)/(ρ_v*L*r_critical) + heat_flux * R_th
    Simplified: ΔT_kinetic = a + b * log(heat_flux) + c * (1/P)
    
    Using representative literature values for kitchen boiling:
    - Base superheat ~0.5-2°C depending on surface conditions
    - Higher heat flux increases superheat
    """
    T_base = boiling_point_from_pressure(pressure)
    
    # Superheat model based on nucleate boiling theory
    # Rohsenow correlation simplified for water at atmospheric pressure
    # ΔT_sat = C_sf * (q / (μ_l * h_fg))^0.33 * (σ / (g*(ρ_l-ρ_v)))^0.5 * (c_p*ΔT/h_fg)^0.33
    # Simplified to: ΔT = k1 * heat_flux^0.33 * P^-0.5
    k1 = 0.001  # Empirical constant
    superheat = k1 * (heat_flux ** 0.33) * (P0 / pressure) ** 0.5
    
    # Add base nucleation superheat (~0.5°C for typical surfaces)
    superheat += 0.5
    
    return T_base + superheat


def dissolved_gas_model(pressure: float, henry_factor: float = 1.0) -> float:
    """
    Dissolved Gas Model: Accounts for boiling point depression due to dissolved gases.
    
    Henry's law: C = k_H * P_gas
    Dissolved gases reduce the partial pressure of water vapor needed for boiling.
    ΔT_gas ≈ -R * T^2 / L_v * ln(1 - x_gas) ≈ -R * T^2 / L_v * x_gas for small x_gas
    
    For typical tap water: ~8-10 mg/L dissolved O2 at 20°C
    Henry's constant for O2 at 20°C: ~1.3 mmol/(L*atm)
    Mole fraction x_gas ~ 1e-5 to 1e-4
    Effect: ~0.01-0.1°C depression
    
    Using representative literature values.
    """
    T_base = boiling_point_from_pressure(pressure)
    
    # Dissolved gas effect - depression of boiling point
    # Typical depression: 0.05-0.2°C for air-saturated water
    # Scales with pressure (lower pressure -> more gas comes out of solution -> larger effect)
    base_depression = 0.1  # °C at 1 atm
    pressure_factor = P0 / pressure  # More gas effect at lower pressure
    
    depression = base_depression * henry_factor * pressure_factor
    
    return T_base - depression


def evaluate_models(data: list[dict]) -> list[dict]:
    """Run all models on field data and compute errors."""
    results = []
    
    for site in data:
        altitude = site["altitude"]
        P_measured = site["P_measured"]
        T_measured = site["boiling_point_measured"]
        
        # Model predictions
        T_isa_baseline = isa_model(altitude)  # ISA using ISA pressure
        T_isa_measured = isa_model_measured_pressure(P_measured)  # ISA physics with measured P
        T_kinetic = kinetic_model(P_measured)
        T_gas = dissolved_gas_model(P_measured)
        
        # Errors (predicted - measured)
        err_isa_baseline = T_isa_baseline - T_measured
        err_isa_measured = T_isa_measured - T_measured
        err_kinetic = T_kinetic - T_measured
        err_gas = T_gas - T_measured
        
        results.append({
            "site_id": site["site_id"],
            "altitude": altitude,
            "P_measured": P_measured,
            "T_measured": T_measured,
            "T_isa_baseline": T_isa_baseline,
            "T_isa_measured": T_isa_measured,
            "T_kinetic": T_kinetic,
            "T_gas": T_gas,
            "err_isa_baseline": err_isa_baseline,
            "err_isa_measured": err_isa_measured,
            "err_kinetic": err_kinetic,
            "err_gas": err_gas,
        })
    
    return results


def compute_metrics(results: list[dict]) -> dict:
    """Compute RMSE and MBE for each model."""
    models = ["isa_baseline", "isa_measured", "kinetic", "gas"]
    metrics = {}
    
    for model in models:
        err_key = f"err_{model}"
        errors = [r[err_key] for r in results if not np.isnan(r[err_key])]
        
        if errors:
            mbe = np.mean(errors)
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            mae = np.mean(np.abs(errors))
            metrics[model] = {
                "MBE": float(mbe),
                "RMSE": float(rmse),
                "MAE": float(mae),
                "N": len(errors)
            }
        else:
            metrics[model] = {"MBE": np.nan, "RMSE": np.nan, "MAE": np.nan, "N": 0}
    
    return metrics


def save_results(results: list[dict], metrics: dict, output_path: str):
    """Save results in exp_gen_sol_out.json format."""
    # Build the output format
    output = {
        "metadata": {
            "method_name": "Boiling Point Model Comparison",
            "description": "Comparison of ISA baseline, Kinetic, and Dissolved Gas models against field measurements",
            "models": ["isa_baseline", "isa_measured", "kinetic", "gas"],
            "metrics": metrics
        },
        "datasets": [
            {
                "dataset": "field_measurements",
                "examples": []
            }
        ]
    }
    
    for r in results:
        example = {
            "input": f"Site: {r['site_id']}, Altitude: {r['altitude']:.1f}m, P_measured: {r['P_measured']:.2f}hPa",
            "output": f"Measured BP: {r['T_measured']:.2f}°C",
            "predict_isa_baseline": f"{r['T_isa_baseline']:.2f}°C",
            "predict_isa_measured": f"{r['T_isa_measured']:.2f}°C",
            "predict_kinetic": f"{r['T_kinetic']:.2f}°C",
            "predict_gas": f"{r['T_gas']:.2f}°C",
            "metadata_altitude": r['altitude'],
            "metadata_P_measured": r['P_measured'],
            "metadata_T_measured": r['T_measured'],
            "metadata_err_isa_baseline": r['err_isa_baseline'],
            "metadata_err_isa_measured": r['err_isa_measured'],
            "metadata_err_kinetic": r['err_kinetic'],
            "metadata_err_gas": r['err_gas'],
        }
        output["datasets"][0]["examples"].append(example)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")


def main():
    logger.info("Starting boiling point model comparison experiment")
    
    # Load data
    data = load_field_data("field_data.json")
    
    # Run models
    results = evaluate_models(data)
    
    # Compute metrics
    metrics = compute_metrics(results)
    
    # Print metrics
    print("\n=== Model Performance Metrics ===")
    for model, m in metrics.items():
        print(f"{model:15s}: RMSE={m['RMSE']:.3f}°C, MBE={m['MBE']:.3f}°C, MAE={m['MAE']:.3f}°C, N={m['N']}")
    
    # Save results
    save_results(results, metrics, "results.json")
    
    # Also save raw results for figure generation
    with open("raw_results.json", "w") as f:
        json.dump({"results": results, "metrics": metrics}, f, indent=2)
    
    logger.info("Experiment completed successfully")


if __name__ == "__main__":
    main()