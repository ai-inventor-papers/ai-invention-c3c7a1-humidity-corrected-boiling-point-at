#!/usr/bin/env python3
"""
Boiling Point Models Evaluation

Implements and evaluates three models for predicting water boiling point at altitude:
1. ISA baseline (dry air International Standard Atmosphere)
2. Humidity-corrected model (moist air thermodynamics with virtual temperature)
3. Local pressure-corrected model (using measured station pressure)

Uses Clausius-Clapeyron relation / Antoine equation for boiling point from pressure.
"""

from loguru import logger
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from typing import Tuple
from scipy import stats

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")


# Physical constants
R_DRY = 287.058  # J/(kg·K) - specific gas constant for dry air
R_VAPOR = 461.495  # J/(kg·K) - specific gas constant for water vapor
G = 9.80665  # m/s² - standard gravity
P0 = 101325.0  # Pa - standard sea level pressure
T0 = 288.15  # K - standard sea level temperature (15°C)
LAPSE_RATE = 0.0065  # K/m - ISA temperature lapse rate

# Antoine equation constants for water (valid 1°C to 100°C)
# log10(P) = A - B/(C+T) where P in mmHg, T in °C
ANTOINE_A = 8.07131
ANTOINE_B = 1730.63
ANTOINE_C = 233.426

# Clausius-Clapeyron constants
L_V = 2.257e6  # J/kg - latent heat of vaporization at 100°C
R_V = 461.5  # J/(kg·K) - gas constant for water vapor


def pressure_to_boiling_point_antoine(pressure_pa: float) -> float:
    """
    Convert pressure to boiling point using Antoine equation.
    
    Antoine: log10(P_mmHg) = A - B/(C + T_°C)
    Solving for T: T = B/(A - log10(P_mmHg)) - C
    
    Args:
        pressure_pa: Pressure in Pascals
        
    Returns:
        Boiling point in °C
    """
    pressure_mmhg = pressure_pa / 133.322  # Convert Pa to mmHg
    if pressure_mmhg <= 0:
        return np.nan
    t_c = ANTOINE_B / (ANTOINE_A - np.log10(pressure_mmhg)) - ANTOINE_C
    return t_c


def pressure_to_boiling_point_clapeyron(pressure_pa: float) -> float:
    """
    Convert pressure to boiling point using Clausius-Clapeyron relation.
    
    ln(P/P0) = -L_v/R_v * (1/T - 1/T0)
    Solving for T: T = 1 / (1/T0 - (R_v/L_v) * ln(P/P0))
    
    Args:
        pressure_pa: Pressure in Pascals
        
    Returns:
        Boiling point in °C
    """
    if pressure_pa <= 0:
        return np.nan
    T0_boil = 373.15  # K - boiling point at standard pressure
    ln_ratio = np.log(pressure_pa / P0)
    t_k = 1.0 / (1.0 / T0_boil - (R_V / L_V) * ln_ratio)
    return t_k - 273.15  # Convert to °C


def isa_pressure(altitude_m: float) -> float:
    """
    Calculate ISA standard atmospheric pressure at given altitude.
    
    For troposphere (0-11 km): P = P0 * (1 - L*h/T0)^(g/(R_d*L))
    
    Args:
        altitude_m: Altitude in meters
        
    Returns:
        Pressure in Pascals
    """
    if altitude_m < 0:
        altitude_m = 0
    if altitude_m > 11000:
        # Above tropopause - simplified
        return 22632.0 * np.exp(-G * (altitude_m - 11000) / (R_DRY * 216.65))
    
    exponent = G / (R_DRY * LAPSE_RATE)
    pressure = P0 * (1.0 - LAPSE_RATE * altitude_m / T0) ** exponent
    return pressure


def isa_temperature(altitude_m: float) -> float:
    """Calculate ISA standard temperature at altitude."""
    if altitude_m < 11000:
        return T0 - LAPSE_RATE * altitude_m
    return 216.65  # Constant in stratosphere


def isa_boiling_point(altitude_m: float) -> float:
    """
    ISA baseline model: boiling point from ISA pressure at altitude.
    
    Args:
        altitude_m: Altitude in meters
        
    Returns:
        Predicted boiling point in °C
    """
    pressure = isa_pressure(altitude_m)
    return pressure_to_boiling_point_clapeyron(pressure)


def saturation_vapor_pressure(t_c: float) -> float:
    """
    Calculate saturation vapor pressure over liquid water (Tetens formula).
    
    Args:
        t_c: Temperature in °C
        
    Returns:
        Saturation vapor pressure in Pa
    """
    # Tetens formula: e_s = 610.78 * exp(17.27 * T / (T + 237.3))
    # where T in °C, result in Pa
    return 610.78 * np.exp(17.27 * t_c / (t_c + 237.3))


def actual_vapor_pressure(t_c: float, rh_percent: float) -> float:
    """
    Calculate actual vapor pressure from temperature and relative humidity.
    
    Args:
        t_c: Temperature in °C
        rh_percent: Relative humidity in percent (0-100)
        
    Returns:
        Actual vapor pressure in Pa
    """
    e_s = saturation_vapor_pressure(t_c)
    return e_s * (rh_percent / 100.0)


def virtual_temperature(t_c: float, e_pa: float, p_pa: float) -> float:
    """
    Calculate virtual temperature for moist air.
    
    T_v = T * (1 + 0.608 * w) where w = 0.622 * e / (p - e)
    Simplified: T_v ≈ T * (1 + 0.378 * e/p)
    
    Args:
        t_c: Temperature in °C
        e_pa: Vapor pressure in Pa
        p_pa: Total pressure in Pa
        
    Returns:
        Virtual temperature in K
    """
    t_k = t_c + 273.15
    # Mixing ratio w = 0.622 * e / (p - e)
    w = 0.622 * e_pa / (p_pa - e_pa) if p_pa > e_pa else 0
    t_v_k = t_k * (1 + 0.608 * w)
    return t_v_k


def humidity_corrected_pressure(altitude_m: float, temp_c: float, rh_percent: float) -> float:
    """
    Calculate pressure at altitude corrected for humidity effects.
    
    Uses hypsometric equation with virtual temperature:
    P = P0 * exp(-g * h / (R_d * T_v_avg))
    
    Where T_v_avg is the layer-averaged virtual temperature.
    We approximate using surface virtual temperature.
    
    Args:
        altitude_m: Altitude in meters
        temp_c: Surface temperature in °C
        rh_percent: Surface relative humidity in percent
        
    Returns:
        Corrected pressure in Pa
    """
    # Get ISA pressure as baseline
    p_isa = isa_pressure(altitude_m)
    
    # Calculate vapor pressure at surface
    e_surface = actual_vapor_pressure(temp_c, rh_percent)
    
    # Surface virtual temperature
    t_v_surface = virtual_temperature(temp_c, e_surface, P0)
    
    # ISA surface temperature (dry)
    t_isa_surface = T0
    
    # Correction factor using virtual temperature
    # Pressure decreases slower in moist air (lower density)
    # P_moist / P_dry ≈ exp(-g*h/R_d * (1/T_v - 1/T_dry))
    if t_v_surface > 0 and t_isa_surface > 0:
        correction = np.exp(-G * altitude_m / R_DRY * (1.0 / t_v_surface - 1.0 / t_isa_surface))
    else:
        correction = 1.0
    
    return p_isa * correction


def humidity_corrected_boiling_point(altitude_m: float, temp_c: float, rh_percent: float) -> float:
    """
    Humidity-corrected model: boiling point using moisture-corrected pressure.
    
    Args:
        altitude_m: Altitude in meters
        temp_c: Temperature in °C
        rh_percent: Relative humidity in percent
        
    Returns:
        Predicted boiling point in °C
    """
    pressure = humidity_corrected_pressure(altitude_m, temp_c, rh_percent)
    return pressure_to_boiling_point_clapeyron(pressure)


def local_pressure_corrected_boiling_point(station_pressure_pa: float) -> float:
    """
    Local pressure-corrected model: boiling point directly from measured station pressure.
    
    Args:
        station_pressure_pa: Measured station pressure in Pa
        
    Returns:
        Predicted boiling point in °C
    """
    return pressure_to_boiling_point_clapeyron(station_pressure_pa)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Compute evaluation metrics.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        Dictionary with metrics
    """
    # Remove NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {"rmse": np.nan, "mae": np.nan, "bias": np.nan, "r2": np.nan, "n": 0}
    
    rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
    mae = np.mean(np.abs(y_true_clean - y_pred_clean))
    bias = np.mean(y_pred_clean - y_true_clean)
    
    # R-squared
    ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
    ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "bias": float(bias),
        "r2": float(r2),
        "n": int(len(y_true_clean))
    }


def paired_ttest(y_true: np.ndarray, y_pred1: np.ndarray, y_pred2: np.ndarray) -> dict:
    """
    Perform paired t-test between two prediction methods.
    
    Args:
        y_true: Ground truth
        y_pred1: Predictions from method 1
        y_pred2: Predictions from method 2
        
    Returns:
        Dictionary with t-statistic, p-value, and interpretation
    """
    mask = ~(np.isnan(y_true) | np.isnan(y_pred1) | np.isnan(y_pred2))
    err1 = np.abs(y_pred1[mask] - y_true[mask])
    err2 = np.abs(y_pred2[mask] - y_true[mask])
    
    if len(err1) < 2:
        return {"t_statistic": float(np.nan), "p_value": float(np.nan), "significant": False}
    
    t_stat, p_val = stats.ttest_rel(err1, err2)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": bool(p_val < 0.05)
    }


@logger.catch(reraise=True)
def main():
    # Load data
    data_path = Path("boiling_point_field_data.csv")
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} data points")
    
    # Verify data
    logger.info(f"Altitude range: {df['altitude_m'].min()} - {df['altitude_m'].max()} m")
    logger.info(f"Measured boiling point range: {df['measured_boiling_point_c'].min():.1f} - {df['measured_boiling_point_c'].max():.1f} °C")
    
    # Apply models
    logger.info("Computing ISA baseline predictions...")
    df['pred_isa'] = df['altitude_m'].apply(isa_boiling_point)
    
    logger.info("Computing humidity-corrected predictions...")
    df['pred_humidity'] = df.apply(
        lambda r: humidity_corrected_boiling_point(r['altitude_m'], r['temp_c'], r['rh_percent']), 
        axis=1
    )
    
    logger.info("Computing local pressure-corrected predictions...")
    df['pred_pressure'] = df['station_pressure_pa'].apply(local_pressure_corrected_boiling_point)
    
    # Compute metrics
    y_true = df['measured_boiling_point_c'].values
    
    metrics_isa = compute_metrics(y_true, df['pred_isa'].values)
    metrics_humidity = compute_metrics(y_true, df['pred_humidity'].values)
    metrics_pressure = compute_metrics(y_true, df['pred_pressure'].values)
    
    logger.info(f"ISA Baseline: RMSE={metrics_isa['rmse']:.3f}, MAE={metrics_isa['mae']:.3f}, Bias={metrics_isa['bias']:.3f}, R²={metrics_isa['r2']:.4f}")
    logger.info(f"Humidity-Corrected: RMSE={metrics_humidity['rmse']:.3f}, MAE={metrics_humidity['mae']:.3f}, Bias={metrics_humidity['bias']:.3f}, R²={metrics_humidity['r2']:.4f}")
    logger.info(f"Local Pressure-Corrected: RMSE={metrics_pressure['rmse']:.3f}, MAE={metrics_pressure['mae']:.3f}, Bias={metrics_pressure['bias']:.3f}, R²={metrics_pressure['r2']:.4f}")
    
    # Paired t-tests
    logger.info("Running paired t-tests...")
    ttest_humidity_vs_isa = paired_ttest(y_true, df['pred_humidity'].values, df['pred_isa'].values)
    ttest_pressure_vs_isa = paired_ttest(y_true, df['pred_pressure'].values, df['pred_isa'].values)
    ttest_pressure_vs_humidity = paired_ttest(y_true, df['pred_pressure'].values, df['pred_humidity'].values)
    
    logger.info(f"Humidity vs ISA: t={ttest_humidity_vs_isa['t_statistic']:.3f}, p={ttest_humidity_vs_isa['p_value']:.4f}, significant={ttest_humidity_vs_isa['significant']}")
    logger.info(f"Pressure vs ISA: t={ttest_pressure_vs_isa['t_statistic']:.3f}, p={ttest_pressure_vs_isa['p_value']:.4f}, significant={ttest_pressure_vs_isa['significant']}")
    logger.info(f"Pressure vs Humidity: t={ttest_pressure_vs_humidity['t_statistic']:.3f}, p={ttest_pressure_vs_humidity['p_value']:.4f}, significant={ttest_pressure_vs_humidity['significant']}")
    
    # Prepare output in exp_gen_sol_out format
    examples = []
    for idx, row in df.iterrows():
        example = {
            "input": f"Altitude: {row['altitude_m']} m, Temp: {row['temp_c']}°C, RH: {row['rh_percent']}%, Station Pressure: {row['station_pressure_pa']} Pa",
            "output": f"Measured boiling point: {row['measured_boiling_point_c']:.1f}°C",
            "metadata_altitude": float(row['altitude_m']),
            "metadata_temp_c": float(row['temp_c']),
            "metadata_rh_percent": float(row['rh_percent']),
            "metadata_station_pressure_pa": float(row['station_pressure_pa']),
            "metadata_measured_bp_c": float(row['measured_boiling_point_c']),
            "predict_isa": f"{float(row['pred_isa']):.3f}",
            "predict_humidity_corrected": f"{float(row['pred_humidity']):.3f}",
            "predict_local_pressure_corrected": f"{float(row['pred_pressure']):.3f}"
        }
        examples.append(example)
    
    output = {
        "metadata": {
            "method_name": "Boiling Point Models Comparison",
            "description": "Comparison of ISA baseline, humidity-corrected, and local pressure-corrected boiling point models",
            "n_samples": len(df),
            "metrics": {
                "isa_baseline": metrics_isa,
                "humidity_corrected": metrics_humidity,
                "local_pressure_corrected": metrics_pressure
            },
            "paired_ttests": {
                "humidity_vs_isa": ttest_humidity_vs_isa,
                "pressure_vs_isa": ttest_pressure_vs_isa,
                "pressure_vs_humidity": ttest_pressure_vs_humidity
            }
        },
        "datasets": [
            {
                "dataset": "boiling_point_field_data",
                "examples": examples
            }
        ]
    }
    
    # Save results
    output_path = Path("results/exp_gen_sol_out.json")
    output_path.write_text(json.dumps(output, indent=2))
    logger.info(f"Saved results to {output_path}")
    
    # Also save CSV for easy inspection
    df.to_csv("results/predictions.csv", index=False)
    logger.info("Saved predictions CSV")
    
    # Print summary table
    print("\n" + "="*70)
    print("BOILING POINT MODEL COMPARISON RESULTS")
    print("="*70)
    print(f"{'Model':<30} {'RMSE (°C)':>12} {'MAE (°C)':>10} {'Bias (°C)':>10} {'R²':>8}")
    print("-"*70)
    print(f"{'ISA Baseline (Dry Air)':<30} {metrics_isa['rmse']:>12.3f} {metrics_isa['mae']:>10.3f} {metrics_isa['bias']:>10.3f} {metrics_isa['r2']:>8.4f}")
    print(f"{'Humidity-Corrected':<30} {metrics_humidity['rmse']:>12.3f} {metrics_humidity['mae']:>10.3f} {metrics_humidity['bias']:>10.3f} {metrics_humidity['r2']:>8.4f}")
    print(f"{'Local Pressure-Corrected':<30} {metrics_pressure['rmse']:>12.3f} {metrics_pressure['mae']:>10.3f} {metrics_pressure['bias']:>10.3f} {metrics_pressure['r2']:>8.4f}")
    print("="*70)
    
    return output


if __name__ == "__main__":
    main()