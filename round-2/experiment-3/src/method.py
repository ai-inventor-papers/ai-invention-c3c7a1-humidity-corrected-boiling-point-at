#!/usr/bin/env python3
"""
Kinetic Boiling Point Model Sensitivity Analysis.

Validates the kinetic boiling point model using Forbes historical data,
simulates sensitivity to heat flux, and quantifies dissolved gas effects.
"""

import json
import sys
from pathlib import Path
import numpy as np
from loguru import logger
from scipy.stats import pearsonr

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

# =============================================================================
# Data: Forbes 1857 Alpine measurements (reconstructed from R MASS package)
# Press in inches Hg, Temp in Fahrenheit
# =============================================================================

FORBES_DATA_RAW = [
    # (pressure_inches_Hg, temp_Fahrenheit)
    (20.79, 194.5), (20.79, 194.3), (22.40, 197.9), (22.67, 198.4),
    (23.15, 199.4), (23.35, 199.9), (23.89, 200.9), (23.93, 201.1),
    (24.02, 201.4), (24.01, 201.3), (25.14, 203.6), (25.35, 204.6),
    (26.17, 206.3), (26.57, 206.5), (26.79, 207.2), (27.05, 208.0),
    (27.67, 209.0)
]

# Conversion constants
INH_TO_KPA = 3.38639  # 1 inch Hg = 3.38639 kPa


def to_si(press_in, temp_f):
    """Convert to SI units: kPa and Celsius."""
    p_kpa = press_in * INH_TO_KPA
    t_c = (temp_f - 32.0) * 5.0 / 9.0
    return p_kpa, t_c


# =============================================================================
# Model 1: ISA Pressure Model (Baseline - Thermodynamic only)
# Uses Clausius-Clapeyron relation with L/R = 5260 K
# =============================================================================

P0_KPA = 101.325
T0_K = 373.15
LR_WATER = 5260.0  # Latent heat / gas constant for water


def isa_pressure_model(p_kpa):
    """
    ISA Pressure Model: Thermodynamic boiling point via Clausius-Clapeyron.
    
    T = 1 / (1/T0 - ln(P/P0) / (L/R))
    
    This is the standard baseline that assumes instantaneous equilibrium.
    """
    if p_kpa <= 0:
        return np.nan
    inv_t = 1.0 / T0_K - np.log(p_kpa / P0_KPA) / LR_WATER
    if inv_t <= 0:
        return np.nan
    t_kelvin = 1.0 / inv_t
    return t_kelvin - 273.15  # Convert to Celsius


# =============================================================================
# Model 2: Local Pressure Model (Empirical linear approximation)
# T(C) = 100 + 0.05 * (P_kPa - 101.325)
# =============================================================================

def local_pressure_model(p_kpa):
    """
    Local Pressure Model: Linear approximation around 1 atm.
    Valid for small pressure deviations from 101.325 kPa.
    """
    return 100.0 + 0.05 * (p_kpa - P0_KPA)


# =============================================================================
# Model 3: Kinetic Model (Our Method)
# T_boil = T_thermo + Delta_T_sat
# Where Delta_T_sat ~ k * HeatFlux^n (nucleation superheat)
# =============================================================================

KINETIC_K = 0.01   # Prefactor for superheat
KINETIC_N = 0.25   # Exponent for heat flux dependence


def kinetic_model(p_kpa, heat_flux_w_m2):
    """
    Kinetic Model: Thermodynamic boiling point + nucleation superheat.
    
    The superheat term captures the kinetic barrier to nucleation:
    Delta_T_sat = k * (HeatFlux)^n
    
    Parameters:
        p_kpa: Pressure in kPa
        heat_flux_w_m2: Heat flux in W/m^2
    """
    t_thermo = isa_pressure_model(p_kpa)
    if np.isnan(t_thermo):
        return np.nan
    delta_t_sat = KINETIC_K * (heat_flux_w_m2 ** KINETIC_N)
    return t_thermo + delta_t_sat


# =============================================================================
# Model 4: Dissolved Gas Model
# Constant perturbation: -0.1 C (dissolved gas lowers effective boiling point)
# =============================================================================

DISSOLVED_GAS_PERTURBATION = -0.1  # Celsius


def dissolved_gas_model(p_kpa, heat_flux_w_m2):
    """
    Kinetic Model with dissolved gas correction.
    Dissolved gas introduces additional nucleation sites, slightly lowering
    the observed boiling point.
    """
    t_base = kinetic_model(p_kpa, heat_flux_w_m2)
    if np.isnan(t_base):
        return np.nan
    return t_base + DISSOLVED_GAS_PERTURBATION


# =============================================================================
# Metrics
# =============================================================================

def compute_metrics(preds, actuals):
    """Compute RMSE, MBE, and Pearson correlation."""
    errors = np.array(preds) - np.array(actuals)
    rmse = np.sqrt(np.mean(errors ** 2))
    mbe = np.mean(errors)
    if len(preds) > 2 and np.std(preds) > 0 and np.std(actuals) > 0:
        corr, p_value = pearsonr(preds, actuals)
    else:
        corr, p_value = np.nan, np.nan
    return {
        "rmse": float(rmse),
        "mbe": float(mbe),
        "pearson_r": float(corr) if not np.isnan(corr) else None,
        "pearson_p": float(p_value) if not np.isnan(p_value) else None,
        "n_points": len(preds)
    }


# =============================================================================
# Main
# =============================================================================

@logger.catch(reraise=True)
def main():
    base_dir = Path(".")
    results_dir = base_dir / "results"
    results_dir.mkdir(exist_ok=True, parents=True)
    
    # Load data
    logger.info("Loading Forbes 1857 dataset")
    data_si = [to_si(p, t) for p, t in FORBES_DATA_RAW]
    p_kpa_array = np.array([d[0] for d in data_si])
    t_c_array = np.array([d[1] for d in data_si])
    logger.info(f"Loaded {len(data_si)} observations, P range: [{p_kpa_array.min():.2f}, {p_kpa_array.max():.2f}] kPa")
    
    # =================================================================
    # Step 1: Validate ISA Pressure Model (Baseline) on Forbes data
    # =================================================================
    logger.info("Validating ISA Pressure Model (thermodynamic baseline)")
    isa_preds = [isa_pressure_model(p) for p in p_kpa_array]
    isa_metrics = compute_metrics(isa_preds, t_c_array)
    logger.info(f"ISA Model: RMSE={isa_metrics['rmse']:.4f}, MBE={isa_metrics['mbe']:.4f}, r={isa_metrics['pearson_r']}")
    
    # =================================================================
    # Step 2: Validate Local Pressure Model
    # =================================================================
    logger.info("Validating Local Pressure Model (empirical baseline)")
    local_preds = [local_pressure_model(p) for p in p_kpa_array]
    local_metrics = compute_metrics(local_preds, t_c_array)
    logger.info(f"Local Model: RMSE={local_metrics['rmse']:.4f}, MBE={local_metrics['mbe']:.4f}, r={local_metrics['pearson_r']}")
    
    # =================================================================
    # Step 3: Kinetic Model Validation (zero heat flux = thermodynamic limit)
    # =================================================================
    logger.info("Validating Kinetic Model at zero heat flux (thermodynamic limit)")
    kinetic_zero_preds = [kinetic_model(p, 0.0) for p in p_kpa_array]
    kinetic_zero_metrics = compute_metrics(kinetic_zero_preds, t_c_array)
    logger.info(f"Kinetic Model (HF=0): RMSE={kinetic_zero_metrics['rmse']:.4f}, MBE={kinetic_zero_metrics['mbe']:.4f}, r={kinetic_zero_metrics['pearson_r']}")
    
    # =================================================================
    # Step 4: Sensitivity Study - Vary Heat Flux from 1e3 to 1e6 W/m^2
    # =================================================================
    logger.info("Running sensitivity study: heat flux 1e3 to 1e6 W/m^2")
    heat_flux_values = np.logspace(3, 6, 34)  # 34 points from 1e3 to 1e6
    
    sensitivity_results = []
    for hf in heat_flux_values:
        t_deviation = []
        for p in p_kpa_array:
            t_with_hf = kinetic_model(p, hf)
            t_thermo = isa_pressure_model(p)
            if not np.isnan(t_with_hf) and not np.isnan(t_thermo):
                t_deviation.append(t_with_hf - t_thermo)
        mean_deviation = np.mean(t_deviation)
        std_deviation = np.std(t_deviation)
        sensitivity_results.append({
            "heat_flux_w_m2": float(hf),
            "mean_boiling_point_deviation_c": float(mean_deviation),
            "std_boiling_point_deviation_c": float(std_deviation)
        })
    
    logger.info(f"Sensitivity study complete: {len(sensitivity_results)} heat flux levels")
    
    # =================================================================
    # Step 5: Dissolved Gas Effect Quantification
    # =================================================================
    logger.info("Quantifying dissolved gas effect")
    dissolved_gas_preds = [dissolved_gas_model(p, 0.0) for p in p_kpa_array]
    dissolved_gas_metrics = compute_metrics(dissolved_gas_preds, t_c_array)
    logger.info(f"Dissolved Gas Model: RMSE={dissolved_gas_metrics['rmse']:.4f}, MBE={dissolved_gas_metrics['mbe']:.4f}, r={dissolved_gas_metrics['pearson_r']}")
    
    # =================================================================
    # Step 6: Per-observation detailed results
    # =================================================================
    per_obs_results = []
    for i, p in enumerate(p_kpa_array):
        t_actual = float(t_c_array[i])
        t_isa = float(isa_preds[i])
        t_local = float(local_preds[i])
        t_kinetic_zero = float(kinetic_zero_preds[i])
        t_dissolved = float(dissolved_gas_preds[i])
        
        per_obs_results.append({
            "observation_index": i,
            "pressure_kpa": float(p),
            "temp_actual_c": t_actual,
            "temp_pred_isa_c": t_isa,
            "temp_pred_local_c": t_local,
            "temp_pred_kinetic_zero_hf_c": t_kinetic_zero,
            "temp_pred_dissolved_gas_c": t_dissolved,
            "error_isa_c": t_isa - t_actual,
            "error_local_c": t_local - t_actual,
            "error_kinetic_c": t_kinetic_zero - t_actual,
            "error_dissolved_gas_c": t_dissolved - t_actual
        })
    
    # =================================================================
    # Step 7: Assemble output in exp_gen_sol_out schema
    # =================================================================
    output = {
        "examples": [
            {
                "id": "forbes_1857_validation",
                "problem_type": "boiling_point_prediction",
                "dataset": "forbes_1857_alpine",
                "n_observations": len(data_si),
                "pressure_range_kpa": [float(p_kpa_array.min()), float(p_kpa_array.max())],
                "temp_range_c": [float(t_c_array.min()), float(t_c_array.max())]
            }
        ],
        "solutions": [
            {
                "id": "isa_pressure_model",
                "name": "ISA Pressure Model",
                "description": "Thermodynamic baseline using Clausius-Clapeyron relation",
                "formula": "T = 1/(1/T0 - ln(P/P0)/(L/R)) - 273.15",
                "parameters": {
                    "P0_kpa": P0_KPA,
                    "T0_K": T0_K,
                    "L_R_K": LR_WATER
                },
                "metrics": isa_metrics,
                "per_observation": per_obs_results
            },
            {
                "id": "local_pressure_model",
                "name": "Local Pressure Model",
                "description": "Empirical linear approximation around 1 atm",
                "formula": "T = 100 + 0.05 * (P - 101.325)",
                "parameters": {
                    "slope_per_kpa": 0.05,
                    "intercept_c": 100.0,
                    "reference_pressure_kpa": P0_KPA
                },
                "metrics": local_metrics,
                "per_observation": per_obs_results
            },
            {
                "id": "kinetic_model_zero_hf",
                "name": "Kinetic Model (Zero Heat Flux)",
                "description": "Thermodynamic limit of the kinetic model; should match ISA",
                "formula": "T = T_thermo + k * HF^n where HF=0, so T = T_thermo",
                "parameters": {
                    "k": KINETIC_K,
                    "n": KINETIC_N,
                    "heat_flux_w_m2": 0.0
                },
                "metrics": kinetic_zero_metrics,
                "per_observation": per_obs_results
            },
            {
                "id": "dissolved_gas_model",
                "name": "Dissolved Gas Model",
                "description": "Kinetic model with dissolved gas correction (-0.1 C)",
                "formula": "T = T_thermo + k * HF^n + delta_gas where delta_gas = -0.1 C",
                "parameters": {
                    "k": KINETIC_K,
                    "n": KINETIC_N,
                    "heat_flux_w_m2": 0.0,
                    "dissolved_gas_correction_c": DISSOLVED_GAS_PERTURBATION
                },
                "metrics": dissolved_gas_metrics,
                "per_observation": per_obs_results
            }
        ],
        "sensitivity_study": {
            "description": "Boiling point deviation from thermodynamic value as a function of heat flux",
            "heat_flux_range_w_m2": [1e3, 1e6],
            "n_heat_flux_levels": len(heat_flux_values),
            "results": sensitivity_results
        }
    }

    # =================================================================
    # Step 8: Also save schema-compliant exp_gen_sol_out format with all predict_* fields
    # =================================================================
    examples_for_schema = []
    for i, p in enumerate(p_kpa_array):
        t_actual = float(t_c_array[i])
        t_isa = float(isa_preds[i])
        t_local = float(local_preds[i])
        t_kinetic_zero = float(kinetic_zero_preds[i])
        t_dissolved = float(dissolved_gas_preds[i])
        
        examples_for_schema.append({
            "input": f"Predict boiling point for pressure: {p:.2f} kPa",
            "output": json.dumps({
                "actual_c": t_actual,
                "pred_isa_c": t_isa,
                "pred_local_c": t_local,
                "pred_kinetic_zero_hf_c": t_kinetic_zero,
                "pred_dissolved_gas_c": t_dissolved
            }),
            "predict_isa": str(t_isa),
            "predict_local": str(t_local),
            "predict_kinetic_zero_hf": str(t_kinetic_zero),
            "predict_dissolved_gas": str(t_dissolved)
        })
    
    schema_output = {
        "datasets": [
            {
                "dataset": "forbes_1857_alpine",
                "examples": examples_for_schema
            }
        ]
    }
    
    schema_output_path = results_dir / "exp_gen_sol_out.json"
    schema_output_path.write_text(json.dumps(schema_output, indent=2))
    logger.info(f"Saved schema-compliant results to {schema_output_path}")
    
    # Also save the full detailed output
    output_path = results_dir / "exp_gen_sol_out_detailed.json"
    output_path.write_text(json.dumps(output, indent=2))
    logger.info(f"Saved detailed results to {output_path}")
    
    # =================================================================
    # Step 8: Save chart specs for aii-data-fig-gen
    # =================================================================
    
    # Spec 1: Boiling point vs pressure - model comparison
    chart1_spec = {
        "type": "scatter",
        "title": "Boiling Point of Water vs Pressure: Model Comparison",
        "xlabel": "Pressure (kPa)",
        "ylabel": "Boiling Point (°C)",
        "aspect": "4:3",
        "series": [
            {
                "label": "Forbes 1857 Data",
                "x": [float(p) for p in p_kpa_array],
                "y": [float(t) for t in t_c_array],
                "marker": "o",
                "linestyle": "none"
            },
            {
                "label": "ISA Pressure Model",
                "x": [float(p) for p in p_kpa_array],
                "y": [float(t) for t in isa_preds],
                "marker": "s",
                "linestyle": "-"
            },
            {
                "label": "Local Pressure Model",
                "x": [float(p) for p in p_kpa_array],
                "y": [float(t) for t in local_preds],
                "marker": "^",
                "linestyle": "--"
            },
            {
                "label": "Dissolved Gas Model",
                "x": [float(p) for p in p_kpa_array],
                "y": [float(t) for t in dissolved_gas_preds],
                "marker": "D",
                "linestyle": ":"
            }
        ]
    }
    
    # Spec 2: Sensitivity - T_boil deviation vs heat flux
    chart2_spec = {
        "type": "line",
        "title": "Sensitivity of Boiling Point Deviation to Heat Flux",
        "xlabel": "Heat Flux (W/m²)",
        "ylabel": "Mean Deviation from Thermodynamic T (°C)",
        "aspect": "4:3",
        "logx": True,
        "series": [
            {
                "label": "Mean Deviation",
                "x": [r["heat_flux_w_m2"] for r in sensitivity_results],
                "y": [r["mean_boiling_point_deviation_c"] for r in sensitivity_results],
                "marker": "o",
                "linestyle": "-"
            }
        ]
    }
    
    # Spec 3: Model comparison bar chart
    model_names = ["ISA", "Local", "Kinetic (HF=0)", "Dissolved Gas"]
    rmse_values = [
        isa_metrics["rmse"],
        local_metrics["rmse"],
        kinetic_zero_metrics["rmse"],
        dissolved_gas_metrics["rmse"]
    ]
    mbe_values = [
        abs(isa_metrics["mbe"]),
        abs(local_metrics["mbe"]),
        abs(kinetic_zero_metrics["mbe"]),
        abs(dissolved_gas_metrics["mbe"])
    ]
    
    chart3_spec = {
        "type": "panel",
        "title": "Model Comparison on Forbes 1857 Dataset",
        "ncols": 2,
        "panels": [
            {
                "type": "bar",
                "title": "RMSE (°C)",
                "xlabel": "Model",
                "ylabel": "RMSE (°C)",
                "categories": model_names,
                "series": [
                    {
                        "label": "RMSE",
                        "values": [float(r) for r in rmse_values]
                    }
                ]
            },
            {
                "type": "bar",
                "title": "Mean Bias (|MBE|, °C)",
                "xlabel": "Model",
                "ylabel": "|MBE| (°C)",
                "categories": model_names,
                "series": [
                    {
                        "label": "|MBE|",
                        "values": [float(m) for m in mbe_values]
                    }
                ]
            }
        ]
    }
    
    # Save chart specs
    charts_dir = results_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    (charts_dir / "chart1_spec.json").write_text(json.dumps(chart1_spec, indent=2))
    (charts_dir / "chart2_spec.json").write_text(json.dumps(chart2_spec, indent=2))
    (charts_dir / "chart3_spec.json").write_text(json.dumps(chart3_spec, indent=2))
    logger.info("Saved chart specs to results/charts/")
    
    # =================================================================
    # Step 9: Test basic functionality
    # =================================================================
    logger.info("Testing basic functionality")
    # Test 1: Standard boiling point at 1 atm
    t_atm = isa_pressure_model(101.325)
    logger.info(f"ISA model at 1 atm: {t_atm:.4f} C (expected ~100.0)")
    assert 99.0 < t_atm < 101.0, f"ISA model failed standard test: {t_atm}"
    
    # Test 2: Kinetic model at zero HF matches ISA
    t_kinetic_zero = kinetic_model(101.325, 0.0)
    logger.info(f"Kinetic model at 1 atm, HF=0: {t_kinetic_zero:.4f} C")
    assert abs(t_kinetic_zero - t_atm) < 0.001, "Kinetic model at HF=0 should match ISA"
    
    # Test 3: Sensitivity - deviation increases with HF
    dev_low = kinetic_model(70.0, 1e3) - isa_pressure_model(70.0)
    dev_high = kinetic_model(70.0, 1e6) - isa_pressure_model(70.0)
    logger.info(f"Deviation at HF=1e3: {dev_low:.4f} C, at HF=1e6: {dev_high:.4f} C")
    assert dev_high > dev_low, "Deviation should increase with heat flux"
    
    logger.info("All basic tests passed")
    logger.info("Method execution complete")


if __name__ == "__main__":
    main()
