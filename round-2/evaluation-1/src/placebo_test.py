#!/usr/bin/env python
"""
Placebo test: shuffle labels and confirm metrics become non-significant.
"""
import json
import numpy as np
from scipy import stats

def main():
    with open("full_method_out.json", "r") as f:
        data = json.load(f)
    
    examples = data["datasets"][0]["examples"]
    n = len(examples)
    
    errors_isa = np.array([ex["metadata_err_isa_baseline"] for ex in examples])
    errors_kinetic = np.array([ex["metadata_err_kinetic"] for ex in examples])
    
    # Real t-statistic
    t_real, _ = stats.ttest_rel(np.abs(errors_isa), np.abs(errors_kinetic))
    print(f"Real paired t-test: t={t_real:.3f}")
    
    # Placebo: shuffle the pairing
    np.random.seed(999)
    n_perm = 10000
    t_shuffled = []
    for _ in range(n_perm):
        # Randomly permute one array
        perm_idx = np.random.permutation(n)
        t_shuf, _ = stats.ttest_rel(np.abs(errors_isa), np.abs(errors_kinetic[perm_idx]))
        t_shuffled.append(t_shuf)
    
    # p-value under shuffled null
    p_shuffled = np.mean(np.abs(t_shuffled) >= np.abs(t_real))
    print(f"Placebo (shuffled) p-value: {p_shuffled:.4f}")
    print(f"Real p-value: {stats.ttest_rel(np.abs(errors_isa), np.abs(errors_kinetic))[1]:.4f}")
    
    if p_shuffled > 0.05:
        print("✓ Placebo test PASSED: Shuffled data shows no significant difference")
    else:
        print("✗ Placebo test FAILED: Shuffled data still shows significance")
    
    # Also test with constant baseline (all zeros)
    errors_zero = np.zeros(n)
    t_zero, p_zero = stats.ttest_rel(np.abs(errors_isa), np.abs(errors_zero))
    print(f"\nConstant zero baseline t-test: t={t_zero:.3f}, p={p_zero:.4f}")
    
    # Test with random noise
    np.random.seed(888)
    errors_random = np.random.normal(0, 0.5, n)
    t_rand, p_rand = stats.ttest_rel(np.abs(errors_isa), np.abs(errors_random))
    print(f"Random noise baseline t-test: t={t_rand:.3f}, p={p_rand:.4f}")

if __name__ == "__main__":
    main()
