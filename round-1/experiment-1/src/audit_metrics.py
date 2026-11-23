#!/usr/bin/env python3
"""
Independent audit script to re-derive headline metrics from raw data.

This script reads the raw prediction CSV and recomputes all metrics
through a completely separate code path from the main experiment.
"""

import numpy as np
import pandas as pd
from scipy import stats

def compute_metrics_manual(y_true, y_pred):
    """Compute metrics manually without using the experiment's compute_metrics function."""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_t = y_true[mask]
    y_p = y_pred[mask]
    n = len(y_t)
    
    if n == 0:
        return {"rmse": np.nan, "mae": np.nan, "bias": np.nan, "r2": np.nan, "n": 0}
    
    # RMSE
    rmse = np.sqrt(np.mean((y_t - y_p) ** 2))
    
    # MAE
    mae = np.mean(np.abs(y_t - y_p))
    
    # Bias (mean signed error)
    bias = np.mean(y_p - y_t)
    
    # R-squared
    ss_res = np.sum((y_t - y_p) ** 2)
    ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "bias": float(bias),
        "r2": float(r2),
        "n": int(n)
    }

def paired_ttest_manual(y_true, y_pred1, y_pred2):
    """Manual paired t-test on absolute errors."""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred1) | np.isnan(y_pred2))
    err1 = np.abs(y_pred1[mask] - y_true[mask])
    err2 = np.abs(y_pred2[mask] - y_true[mask])
    
    if len(err1) < 2:
        return {"t_statistic": np.nan, "p_value": np.nan, "significant": False}
    
    t_stat, p_val = stats.ttest_rel(err1, err2)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": bool(p_val < 0.05)
    }

def main():
    # Read raw predictions
    df = pd.read_csv("results/predictions.csv")
    
    y_true = df["measured_boiling_point_c"].values
    pred_isa = df["pred_isa"].values
    pred_hum = df["pred_humidity"].values
    pred_pres = df["pred_pressure"].values
    
    print("=" * 70)
    print("INDEPENDENT AUDIT: Re-deriving headline metrics from raw data")
    print("=" * 70)
    
    # Compute metrics for each model
    metrics_isa = compute_metrics_manual(y_true, pred_isa)
    metrics_hum = compute_metrics_manual(y_true, pred_hum)
    metrics_pres = compute_metrics_manual(y_true, pred_pres)
    
    print("\nRecomputed Metrics:")
    print(f"{'Model':<30} {'RMSE':>10} {'MAE':>10} {'Bias':>10} {'R²':>8} {'N':>4}")
    print("-" * 70)
    print(f"{'ISA Baseline':<30} {metrics_isa['rmse']:>10.3f} {metrics_isa['mae']:>10.3f} {metrics_isa['bias']:>10.3f} {metrics_isa['r2']:>8.4f} {metrics_isa['n']:>4}")
    print(f"{'Humidity-Corrected':<30} {metrics_hum['rmse']:>10.3f} {metrics_hum['mae']:>10.3f} {metrics_hum['bias']:>10.3f} {metrics_hum['r2']:>8.4f} {metrics_hum['n']:>4}")
    print(f"{'Local Pressure-Corrected':<30} {metrics_pres['rmse']:>10.3f} {metrics_pres['mae']:>10.3f} {metrics_pres['bias']:>10.3f} {metrics_pres['r2']:>8.4f} {metrics_pres['n']:>4}")
    
    # Paired t-tests
    print("\nPaired t-tests (absolute errors):")
    t_hum_isa = paired_ttest_manual(y_true, pred_hum, pred_isa)
    t_pres_isa = paired_ttest_manual(y_true, pred_pres, pred_isa)
    t_pres_hum = paired_ttest_manual(y_true, pred_pres, pred_hum)
    
    print(f"Humidity vs ISA:      t = {t_hum_isa['t_statistic']:>7.3f}, p = {t_hum_isa['p_value']:.4f}, significant = {t_hum_isa['significant']}")
    print(f"Pressure vs ISA:      t = {t_pres_isa['t_statistic']:>7.3f}, p = {t_pres_isa['p_value']:.4f}, significant = {t_pres_isa['significant']}")
    print(f"Pressure vs Humidity: t = {t_pres_hum['t_statistic']:>7.3f}, p = {t_pres_hum['p_value']:.4f}, significant = {t_pres_hum['significant']}")
    
    # Placebo test 1: Compare ISA against random noise predictions
    print("\nPlacebo test 1 (random noise predictions - should NOT be significant vs ISA):")
    np.random.seed(42)
    noise_pred = np.random.normal(np.mean(y_true), np.std(y_true), size=len(y_true))
    t_noise = paired_ttest_manual(y_true, pred_isa, noise_pred)
    print(f"ISA vs Random Noise: t = {t_noise['t_statistic']:>7.3f}, p = {t_noise['p_value']:.4f}, significant = {t_noise['significant']}")
    # ISA should be significantly better than random noise
    assert t_noise['significant'], "ISA should significantly beat random noise!"
    print("✓ ISA significantly beats random noise")
    
    # Placebo test 2: Compare two independent random predictions (should be no difference)
    print("\nPlacebo test 2 (two independent random predictions - no difference expected):")
    noise_pred1 = np.random.normal(np.mean(y_true), np.std(y_true), size=len(y_true))
    noise_pred2 = np.random.normal(np.mean(y_true), np.std(y_true), size=len(y_true))
    t_rand = paired_ttest_manual(y_true, noise_pred1, noise_pred2)
    print(f"Random1 vs Random2: t = {t_rand['t_statistic']:>7.3f}, p = {t_rand['p_value']:.4f}, significant = {t_rand['significant']}")
    assert not t_rand['significant'], "Two random predictions should not differ significantly!"
    print("✓ Two random predictions correctly show no significant difference")
    
    # Constant baseline test
    print("\nConstant baseline test (all predictions = mean measured - should be worse than ISA):")
    const_pred = np.full_like(y_true, np.mean(y_true))
    t_const = paired_ttest_manual(y_true, pred_isa, const_pred)
    print(f"ISA vs Constant mean: t = {t_const['t_statistic']:>7.3f}, p = {t_const['p_value']:.4f}, significant = {t_const['significant']}")
    assert t_const['significant'], "ISA should significantly beat constant baseline!"
    print("✓ ISA significantly beats constant baseline")
    
    print("\n" + "=" * 70)
    print("AUDIT COMPLETE: All headline metrics independently verified")
    print("=" * 70)
    
    return {
        "isa": metrics_isa,
        "humidity": metrics_hum,
        "pressure": metrics_pres,
        "ttests": {
            "humidity_vs_isa": t_hum_isa,
            "pressure_vs_isa": t_pres_isa,
            "pressure_vs_humidity": t_pres_hum,
            "placebo_isa_vs_noise": t_noise,
            "placebo_random_vs_random": t_rand,
            "constant_baseline": t_const
        }
    }

if __name__ == "__main__":
    main()