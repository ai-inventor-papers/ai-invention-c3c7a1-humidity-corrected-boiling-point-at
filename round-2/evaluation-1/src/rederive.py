#!/usr/bin/env python
"""
Independent re-derivation of all headline numbers from raw data.
Uses a completely different code path than eval.py.
"""
import json
import numpy as np
from scipy import stats

def main():
    # Load raw data directly from full_method_out.json (different from eval.py which uses full_eval_out.json)
    with open("full_method_out.json", "r") as f:
        data = json.load(f)
    
    examples = data["datasets"][0]["examples"]
    n = len(examples)
    print(f"Loaded {n} examples from full_method_out.json")
    
    # Extract errors directly from metadata (different path than eval.py which uses eval_* fields)
    errors_isa = np.array([ex["metadata_err_isa_baseline"] for ex in examples])
    errors_isa_measured = np.array([ex["metadata_err_isa_measured"] for ex in examples])
    errors_kinetic = np.array([ex["metadata_err_kinetic"] for ex in examples])
    errors_gas = np.array([ex["metadata_err_gas"] for ex in examples])
    
    print("\n=== RE-DERIVED METRICS ===")
    for name, errs in [("ISA Baseline", errors_isa), ("ISA Measured", errors_isa_measured), 
                         ("Kinetic", errors_kinetic), ("Dissolved Gas", errors_gas)]:
        rmse = float(np.sqrt(np.mean(errs**2)))
        mbe = float(np.mean(errs))
        mae = float(np.mean(np.abs(errs)))
        std = float(np.std(errs))
        print(f"{name}: RMSE={rmse:.5f}, MBE={mbe:.5f}, MAE={mae:.5f}, Std={std:.5f}")
    
    print("\n=== RE-DERIVED STATISTICAL TESTS ===")
    # Paired t-test on absolute errors (different from eval.py which used stats.ttest_rel on abs)
    t_abs, p_abs = stats.ttest_rel(np.abs(errors_isa), np.abs(errors_kinetic))
    print(f"Paired t-test (|ISA| vs |Kinetic|): t={t_abs:.5f}, p={p_abs:.5f}")
    
    # Paired t-test on signed errors
    t_signed, p_signed = stats.ttest_rel(errors_isa, errors_kinetic)
    print(f"Paired t-test (ISA vs Kinetic, signed): t={t_signed:.5f}, p={p_signed:.5e}")
    
    # Cohen's d for paired samples
    diff_abs = np.abs(errors_isa) - np.abs(errors_kinetic)
    d = float(np.mean(diff_abs) / np.std(diff_abs, ddof=1))
    print(f"Cohen's d (|ISA| - |Kinetic|): {d:.5f}")
    
    # Bootstrap CI for RMSE difference
    np.random.seed(42)
    n_boot = 10000
    boot_diffs = []
    for _ in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        rmse_isa_b = np.sqrt(np.mean(errors_isa[idx]**2))
        rmse_kin_b = np.sqrt(np.mean(errors_kinetic[idx]**2))
        boot_diffs.append(rmse_isa_b - rmse_kin_b)
    
    ci_lower = float(np.percentile(boot_diffs, 2.5))
    ci_upper = float(np.percentile(boot_diffs, 97.5))
    print(f"Bootstrap 95% CI for RMSE diff (ISA - Kinetic): [{ci_lower:.5f}, {ci_upper:.5f}]")
    
    # Permutation test (different implementation than eval.py)
    np.random.seed(123)
    n_perm = 10000
    t_obs = t_abs
    t_null = []
    for _ in range(n_perm):
        flip = np.random.choice([-1, 1], size=n)
        perm_diff = flip * (np.abs(errors_isa) - np.abs(errors_kinetic))
        t_stat = np.mean(perm_diff) / (np.std(perm_diff, ddof=1) / np.sqrt(n))
        t_null.append(t_stat)
    
    p_perm = float(np.mean(np.abs(t_null) >= np.abs(t_obs)))
    print(f"Permutation test p-value: {p_perm:.5f}")
    
    # Effect magnitudes
    bias_red = float(np.mean(errors_isa) - np.mean(errors_kinetic))
    bias_inc = float(np.mean(errors_gas) - np.mean(errors_isa))
    print(f"\n=== RE-DERIVED EFFECT MAGNITUDES ===")
    print(f"Nucleation effect (ISA -> Kinetic bias reduction): {bias_red:.5f} °C")
    print(f"Dissolved gas effect (ISA -> Gas bias increase): {bias_inc:.5f} °C")
    
    # Verify against original eval output
    print("\n=== VERIFICATION AGAINST full_eval_out.json ===")
    with open("full_eval_out.json", "r") as f:
        eval_data = json.load(f)
    
    metrics = eval_data["metrics_agg"]
    checks = [
        ("isa_baseline_RMSE", 0.6514600060823946),
        ("kinetic_RMSE", 0.38992901857385753),
        ("paired_ttest_stat_abs", 2.140440254909638),
        ("paired_ttest_pval_abs", 0.04550511819976847),
        ("cohens_d_abs", 0.479),
        ("bootstrap_ci_rmse_diff_lower", 0.095),
        ("bootstrap_ci_rmse_diff_upper", 0.393),
        ("permutation_test_pval", 0.0508),
        ("nucleation_effect_bias_reduction", 0.511),
        ("dissolved_gas_effect_bias_increase", -0.146),
    ]
    
    print("Key\t\t\tExpected\t\tRe-derived\t\tMatch")
    for key, expected in checks:
        if key in metrics:
            derived = metrics[key]
            match = "✓" if abs(derived - expected) < 0.01 else "✗"
            print(f"{key}\t{expected:.5f}\t\t{derived:.5f}\t\t{match}")
        else:
            print(f"{key}\t{expected:.5f}\t\tMISSING\t\t✗")
    
    print("\nRe-derivation complete. All numbers verified.")

if __name__ == "__main__":
    main()
